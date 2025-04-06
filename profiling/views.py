
# Create your views here.
from django.http import  JsonResponse
from pymongo import MongoClient
from rest_framework.views import APIView
import datetime
import json
import requests
import pytz

iran_tz = pytz.timezone('Asia/Tehran')

client = MongoClient(port=27017)
 
db = client['sejamProfile_DRF']

def generate_acceses_token():
    global db
    current_datetime = datetime.datetime.now(iran_tz)
    url = "https://api.sejam.ir:8080/v1.1/accessToken"
    headers = {"accept": "application/json","Content-Type": "application/json-patch+json"}    
    data = {"username": "911","password": "D@f4d38bn" }
                                        
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response=response.json()
    ttl_str = response['data']['ttl']  # Time duration string in 'HH:MM:SS' format
    ttl_components = ttl_str.split(':')
    ttl_duration = datetime.timedelta(hours=int(ttl_components[0]), minutes=int(ttl_components[1]), seconds=int(ttl_components[2]))
    ttl_time = current_datetime + ttl_duration
    tehran_tz = pytz.timezone("Asia/Tehran")
    ttl_time = ttl_time.astimezone(tehran_tz)

    acceses_token = {'token':response['data']['accessToken'],'TokenEndTime':str(ttl_time)}
    db.token.drop()
    db.token.insert_one(acceses_token) 


def OTP(sh_id):
    global db
    try:
        acceses_token_dana=list(client['sejamProfile_DRF'].token.find())[0]
        acceses_token_dana['TokenEndTime']=datetime.datetime.strptime(acceses_token_dana['TokenEndTime'], "%Y-%m-%d %H:%M:%S.%f%z")

        # print(acceses_token_dana['TokenEndTime'])
        # print(acceses_token_dana['TokenEndTime']<datetime.datetime.now(iran_tz))
        # print(acceses_token_dana['TokenEndTime'],datetime.datetime.now(iran_tz))
        if acceses_token_dana['TokenEndTime']<datetime.datetime.now(iran_tz):
            print('reloading access token')
            generate_acceses_token()
            acceses_token_dana=list(client['sejamProfile_DRF'].token.find())[0]
            acceses_token_dana['TokenEndTime']=datetime.datetime.strptime(acceses_token_dana['TokenEndTime'], "%Y-%m-%d %H:%M:%S.%f%z")
            print(acceses_token_dana['TokenEndTime'])
    except:
        print('genrating access token')
        generate_acceses_token() 
        
    acceses_token_dana=list(client['sejamProfile_DRF'].token.find())[0]
    acceses_token_dana['TokenEndTime']=datetime.datetime.strptime(acceses_token_dana['TokenEndTime'], "%Y-%m-%d %H:%M:%S.%f%z")

    print(acceses_token_dana['TokenEndTime'])
    url = "https://api.sejam.ir:8080/v1.1/kycOtp"
    data = {"uniqueIdentifier":sh_id}
    headers = {"accept": "application/json","Content-Type": "application/json-patch+json", "Authorization": "bearer "+acceses_token_dana['token'] }
    a=requests.post(url, headers=headers, data=json.dumps(data))
    return {'id':sh_id,'status':a.status_code}
def profile_sejam(sh_id,otpCode):
    global db
    otp=otpCode
    try:
        acceses_token_dana=list(client['sejamProfile_DRF'].token.find())[0]
        acceses_token_dana['TokenEndTime']=datetime.datetime.strptime(acceses_token_dana['TokenEndTime'], "%Y-%m-%d %H:%M:%S.%f%z")
        if acceses_token_dana['TokenEndTime']<datetime.datetime.now(iran_tz):
            print('reloading access token')
            generate_acceses_token()
            acceses_token_dana=list(client['sejamProfile_DRF'].token.find())[0]
            acceses_token_dana['TokenEndTime']=datetime.datetime.strptime(acceses_token_dana['TokenEndTime'], "%Y-%m-%d %H:%M:%S.%f%z")

    except:
        print('generate access token')
        generate_acceses_token()
        acceses_token_dana=list(client['sejamProfile_DRF'].token.find())[0]
        acceses_token_dana['TokenEndTime']=datetime.datetime.strptime(acceses_token_dana['TokenEndTime'], "%Y-%m-%d %H:%M:%S.%f%z")

        
    
    base_url = f"https://api.sejam.ir:8080/v1.1/servicesWithOtp/profiles/{sh_id}"
    url = f"{base_url}?otp={otp}"
    
    headers = {
                "accept": "application/json",
                "Content-Type": "application/json-patch+json",
                "Authorization": "bearer "+acceses_token_dana['token']
              }
    try:
        response = requests.get(url, headers=headers)
        # print(response.json())
        # print('\n---------------------------------------------------------------------------------------------------------')
        res=response.json()
        db.profile.insert_one({'id':str(res['data']['mobile']),'data':res['data']}) 
        if res['data']['type']=='IranianPrivatePerson':
            pInf={'uniqueIdentifier':   str(res['data']['uniqueIdentifier']).strip(),
                  'type':               str(res['data']['type']).strip(),
                  'firstName ':         str(res['data']['privatePerson']['firstName']).strip(),
                  'lastName':           str(res['data']['privatePerson']['lastName']).strip(),
                  'fatherName':         str(res['data']['privatePerson']['fatherName']).strip(),
                  'gender':             str(res['data']['privatePerson']['gender']).strip(),
                  'birthDate':          str(res['data']['privatePerson']['birthDate']).strip(),
                  'placeOfBirth':       str(res['data']['privatePerson']['placeOfBirth']).strip(),
                  'placeOfIssue':       str(res['data']['privatePerson']['placeOfIssue']).strip(),
                  'mobile':             str(res['data']['mobile']).strip(),
                  'email':              str(res['data']['email']).strip()   ,
                  'tradeCode':          str(res['data']['tradingCodes'][0]['code']).strip(),
                  'sheba':              str(res['data']['accounts'][0]['sheba']).strip(),
                  'bank_name      ':    str(res['data']['accounts'][0]['bank']['name']).strip(),
                  'bank_branchCode':    str(res['data']['accounts'][0]['branchCode']).strip(),
                  'bank_branchName':    str(res['data']['accounts'][0]['branchName']).strip(),
                  'bank_branchCity':    str(res['data']['accounts'][0]['branchCity']['name']).strip(),
                  'bank_accountNumber': str(res['data']['accounts'][0]['accountNumber']).strip(),
                  }
        elif  res['data']['type']=='IranianLegalPerson':
            SHR={}
            for i in res['data']['legalPersonShareholders']:
                SHR[i['uniqueIdentifier']]={'Name':i['firstName'].strip(),'LastName':i['lastName'].strip(),'position':i['positionType']}
            persian_positions = {
                                    'Chairman': 'رئیس هیئت مدیره',
                                    'Ceo': 'مدیرعامل',
                                    'Member': 'عضو هیئت مدیره',
                                    'DeputyChairman': 'نایب رئیس هیئت مدیره'
                                }
                                
            for key, value in SHR.items():
                position = value['position']
                persian_position = persian_positions.get(position)
                if persian_position:
                    value['position'] = persian_position   
            pInf={'uniqueIdentifier':   str(res['data']['uniqueIdentifier']).strip(),
                  'type':               str(res['data']['type']).strip(),
                  'companyName ':       str(res['data']['legalPerson']['companyName']).strip(),
                  'economicCode':       str(res['data']['legalPerson']['economicCode']).strip(),
                  'registerDate':       str(res['data']['legalPerson']['registerDate']).strip(),
                  'registerPlace':      str(res['data']['legalPerson']['registerPlace']).strip(),
                  'registerNumber':     str(res['data']['legalPerson']['registerNumber']).strip(),
                  'shareHolders':       SHR,
                  'mobile':             str(res['data']['mobile']).strip(),
                  'email':              str(res['data']['email']).strip(),
                  'tradeCode':          str(res['data']['tradingCodes']).strip(),
                  'sheba':              str(res['data']['accounts'][0]['sheba']).strip(),
                  'bank_name      ':    str(res['data']['accounts'][0]['bank']['name']).strip(),
                  'bank_branchCode':    str(res['data']['accounts'][0]['branchCode']).strip(),
                  'bank_branchName':    str(res['data']['accounts'][0]['branchName']).strip(),
                  'bank_branchCity':    str(res['data']['accounts'][0]['branchCity']['name']).strip(),
                  'bank_accountNumber': str(res['data']['accounts'][0]['accountNumber']).strip(),
                  }
        return pInf
        
    except:
        db.Errors.insert_one({'data':response.text}) 
        if 'error' in response.json():
            if response.json()['error']['customMessage']=='invalid otp':
                return {'error':'invalid OTP'}
        else:
            return {'error':'somthing went wrong'}
        
###___________________________________________________________________________________________________________________________________________###
###___________________________________________________________________________________________________________________________________________###
###___________________________________________________________________________________________________________________________________________###
###___________________________________________________________________________________________________________________________________________###


class GetOTPView(APIView):
    def get(self, request, sh_id, format=None):
        data=OTP(str(sh_id))
        response=JsonResponse(data, safe=False ,json_dumps_params={'ensure_ascii': False})
        response["Access-Control-Allow-Origin"] = "*"
        response['Content-Type']= 'application/json'
        response['Charset']= 'utf-8'
        response["Access-Control-Allow-Methods"] = "GET"
        response["Access-Control-Max-Age"] = "1000"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
        return response
        

class ValidateOTPView(APIView):
    def get(self, request,sh_id, otpCode, format=None):
        data=profile_sejam(str(sh_id), str(otpCode))
        response=JsonResponse(data, safe=False ,json_dumps_params={'ensure_ascii': False})
        response["Access-Control-Allow-Origin"] = "*"
        response['Content-Type']= 'application/json'
        response['Charset']= 'utf-8'
        response["Access-Control-Allow-Methods"] = "GET"
        response["Access-Control-Max-Age"] = "1000"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
        return response
       
