"""
Views for the profiling app.

This module provides API endpoints for the Sejam service integration,
including requesting OTPs and validating them to retrieve user profiles.
"""

import json
import logging
import datetime
import pytz
import requests

from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status

from .models import AccessToken, Profile, Shareholder, ErrorLog

# Configure logging
logger = logging.getLogger(__name__)
iran_tz = pytz.timezone('Asia/Tehran')


def generate_access_token():
    """
    Generate a new access token from the Sejam API.
    
    Returns:
        AccessToken: The new access token object
    """
    current_datetime = datetime.datetime.now(iran_tz)
    url = f"{settings.SEJAM_API_BASE_URL}/accessToken"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json-patch+json"
    }
    
    data = {
        "username": settings.SEJAM_API_USERNAME,
        "password": settings.SEJAM_API_PASSWORD
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()
        
        # Calculate token expiration time
        ttl_str = response_data['data']['ttl']
        ttl_components = ttl_str.split(':')
        ttl_duration = datetime.timedelta(
            hours=int(ttl_components[0]),
            minutes=int(ttl_components[1]),
            seconds=int(ttl_components[2])
        )
        ttl_time = current_datetime + ttl_duration
        ttl_time = ttl_time.astimezone(iran_tz)
        
        # Delete old tokens and save new one
        AccessToken.objects.all().delete()
        token = AccessToken.objects.create(
            token=response_data['data']['accessToken'],
            token_end_time=ttl_time
        )
        
        return token
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating access token: {str(e)}")
        ErrorLog.objects.create(error_data=str(e))
        raise


def get_valid_token():
    """
    Get a valid access token. If no valid token exists, generate a new one.
    
    Returns:
        str: Valid access token
    """
    try:
        # Try to get the latest token
        token = AccessToken.objects.latest('created_at')
        
        # Check if token is expired
        if token.token_end_time < datetime.datetime.now(iran_tz):
            logger.info("Access token expired, generating new one")
            token = generate_access_token()
            
    except AccessToken.DoesNotExist:
        logger.info("No access token found, generating new one")
        token = generate_access_token()
        
    return token.token


def request_otp(sh_id):
    """
    Request an OTP from the Sejam API for a given identifier.
    
    Args:
        sh_id (str): The unique identifier for the user
        
    Returns:
        dict: Response data with status information
    """
    token = get_valid_token()
    
    url = f"{settings.SEJAM_API_BASE_URL}/kycOtp"
    data = {"uniqueIdentifier": sh_id}
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json-patch+json",
        "Authorization": f"bearer {token}"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return {'id': sh_id, 'status': response.status_code}
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error requesting OTP: {str(e)}")
        ErrorLog.objects.create(error_data=response.text if 'response' in locals() else str(e))
        return {'id': sh_id, 'status': e.response.status_code if hasattr(e, 'response') else 500, 'error': str(e)}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting OTP: {str(e)}")
        ErrorLog.objects.create(error_data=str(e))
        return {'id': sh_id, 'status': 500, 'error': 'Connection error'}


def get_profile(sh_id, otp_code):
    """
    Validate OTP and retrieve user profile from Sejam API.
    
    Args:
        sh_id (str): The unique identifier for the user
        otp_code (str): The OTP code to validate
        
    Returns:
        dict: Structured profile data or error information
    """
    token = get_valid_token()
    
    base_url = f"{settings.SEJAM_API_BASE_URL}/servicesWithOtp/profiles/{sh_id}"
    url = f"{base_url}?otp={otp_code}"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json-patch+json",
        "Authorization": f"bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        res = response.json()
        
        # Store raw data
        profile_data = res['data']
        
        # Try to get existing profile or create new one
        profile, created = Profile.objects.update_or_create(
            unique_identifier=profile_data['uniqueIdentifier'],
            defaults={
                'person_type': profile_data['type'],
                'mobile': profile_data['mobile'],
                'email': profile_data.get('email', ''),
                'raw_data': profile_data
            }
        )
        
        # Process person-specific data
        if profile_data['type'] == 'IranianPrivatePerson':
            person_data = profile_data['privatePerson']
            profile.first_name = person_data.get('firstName', '').strip()
            profile.last_name = person_data.get('lastName', '').strip()
            profile.father_name = person_data.get('fatherName', '').strip()
            profile.gender = person_data.get('gender', '').strip()
            profile.birth_date = person_data.get('birthDate', '').strip()
            profile.place_of_birth = person_data.get('placeOfBirth', '').strip()
            profile.place_of_issue = person_data.get('placeOfIssue', '').strip()
            
        elif profile_data['type'] == 'IranianLegalPerson':
            legal_data = profile_data['legalPerson']
            profile.company_name = legal_data.get('companyName', '').strip()
            profile.economic_code = legal_data.get('economicCode', '').strip()
            profile.register_date = legal_data.get('registerDate', '').strip()
            profile.register_place = legal_data.get('registerPlace', '').strip()
            profile.register_number = legal_data.get('registerNumber', '').strip()
            
            # Process shareholders
            persian_positions = {
                'Chairman': 'رئیس هیئت مدیره',
                'Ceo': 'مدیرعامل',
                'Member': 'عضو هیئت مدیره',
                'DeputyChairman': 'نایب رئیس هیئت مدیره'
            }
            
            # Clear existing shareholders and add new ones
            profile.shareholders.all().delete()
            for shareholder in profile_data.get('legalPersonShareholders', []):
                position = shareholder.get('positionType', '')
                persian_position = persian_positions.get(position, position)
                
                Shareholder.objects.create(
                    profile=profile,
                    unique_identifier=shareholder.get('uniqueIdentifier', ''),
                    first_name=shareholder.get('firstName', '').strip(),
                    last_name=shareholder.get('lastName', '').strip(),
                    position=persian_position
                )
        
        # Bank information - with safe field access
        if profile_data.get('tradingCodes') and len(profile_data['tradingCodes']) > 0:
            profile.trade_code = profile_data['tradingCodes'][0].get('code', '').strip()
            
        if profile_data.get('accounts') and len(profile_data['accounts']) > 0:
            account = profile_data['accounts'][0]
            profile.sheba = account.get('sheba', '').strip()
            profile.bank_account_number = account.get('accountNumber', '').strip()
            profile.bank_branch_code = account.get('branchCode', '').strip()
            profile.bank_branch_name = account.get('branchName', '').strip()
            
            # Safe access to bank name
            if account.get('bank') and account['bank']:
                profile.bank_name = account['bank'].get('name', '').strip()
                
            # Safe access to branch city - this is where the error was occurring
            if account.get('branchCity') and account['branchCity']:
                profile.bank_branch_city = account['branchCity'].get('name', '').strip()
        
        profile.save()
        
        # Format response
        if profile.person_type == 'IranianPrivatePerson':
            return {
                'uniqueIdentifier': profile.unique_identifier,
                'type': profile.person_type,
                'firstName': profile.first_name,
                'lastName': profile.last_name,
                'fatherName': profile.father_name,
                'gender': profile.gender,
                'birthDate': profile.birth_date,
                'placeOfBirth': profile.place_of_birth,
                'placeOfIssue': profile.place_of_issue,
                'mobile': profile.mobile,
                'email': profile.email,
                'tradeCode': profile.trade_code,
                'sheba': profile.sheba,
                'bank_name': profile.bank_name,
                'bank_branchCode': profile.bank_branch_code,
                'bank_branchName': profile.bank_branch_name,
                'bank_branchCity': profile.bank_branch_city,
                'bank_accountNumber': profile.bank_account_number,
            }
        else:
            # Process shareholders for response
            shareholders = {}
            for sh in profile.shareholders.all():
                shareholders[sh.unique_identifier] = {
                    'Name': sh.first_name,
                    'LastName': sh.last_name,
                    'position': sh.position
                }
                
            return {
                'uniqueIdentifier': profile.unique_identifier,
                'type': profile.person_type,
                'companyName': profile.company_name,
                'economicCode': profile.economic_code,
                'registerDate': profile.register_date,
                'registerPlace': profile.register_place,
                'registerNumber': profile.register_number,
                'shareHolders': shareholders,
                'mobile': profile.mobile,
                'email': profile.email,
                'tradeCode': profile.trade_code,
                'sheba': profile.sheba,
                'bank_name': profile.bank_name,
                'bank_branchCode': profile.bank_branch_code,
                'bank_branchName': profile.bank_branch_name,
                'bank_branchCity': profile.bank_branch_city,
                'bank_accountNumber': profile.bank_account_number,
            }
            
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error retrieving profile: {str(e)}")
        ErrorLog.objects.create(error_data=response.text if 'response' in locals() else str(e))
        
        # Check for invalid OTP error
        if hasattr(e, 'response') and e.response.status_code == 400:
            try:
                error_data = e.response.json()
                if 'error' in error_data and error_data['error'].get('customMessage') == 'invalid otp':
                    return {'error': 'invalid OTP'}
            except ValueError:
                pass
                
        return {'error': 'Error retrieving profile data'}
        
    except Exception as e:
        logger.error(f"Error retrieving profile: {str(e)}")
        ErrorLog.objects.create(error_data=str(e))
        return {'error': 'Something went wrong'}

class GetOTPView(APIView):
    """API view to request an OTP for a user."""
    throttle_classes = [AnonRateThrottle]
    
    def get(self, request, sh_id, format=None):
        """
        Get an OTP for the specified user ID.
        
        Args:
            request: The HTTP request
            sh_id: The unique identifier for the user
            format: The response format
            
        Returns:
            Response: JSON response with OTP request status
        """
        data = request_otp(str(sh_id))
        return Response(data)


class ValidateOTPView(APIView):
    """API view to validate an OTP and retrieve user profile."""
    throttle_classes = [AnonRateThrottle]
    
    def get(self, request, sh_id, otpCode, format=None):
        """
        Validate OTP and return user profile data.
        
        Args:
            request: The HTTP request
            sh_id: The unique identifier for the user
            otpCode: The OTP code to validate
            format: The response format
            
        Returns:
            Response: JSON response with profile data or error
        """
        data = get_profile(str(sh_id), str(otpCode))
        return Response(data)