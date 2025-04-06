from django.db import models

class AccessToken(models.Model):
    """Store and manage access tokens for Sejam API."""
    token = models.CharField(max_length=255)
    token_end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Access Token"
        verbose_name_plural = "Access Tokens"
    
    def __str__(self):
        return f"Token valid until {self.token_end_time}"


class Profile(models.Model):
    """Store user profile data retrieved from Sejam API."""
    PERSON_TYPE_CHOICES = [
        ('IranianPrivatePerson', 'Iranian Private Person'),
        ('IranianLegalPerson', 'Iranian Legal Person'),
    ]
    
    unique_identifier = models.CharField(max_length=20, primary_key=True)
    person_type = models.CharField(max_length=30, choices=PERSON_TYPE_CHOICES)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    
    # Private person fields
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birth_date = models.CharField(max_length=20, blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)
    place_of_issue = models.CharField(max_length=100, blank=True, null=True)
    
    # Legal person fields
    company_name = models.CharField(max_length=200, blank=True, null=True)
    economic_code = models.CharField(max_length=30, blank=True, null=True)
    register_date = models.CharField(max_length=20, blank=True, null=True)
    register_place = models.CharField(max_length=100, blank=True, null=True)
    register_number = models.CharField(max_length=30, blank=True, null=True)
    
    # Bank information
    trade_code = models.CharField(max_length=30, blank=True, null=True)
    sheba = models.CharField(max_length=30, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_branch_code = models.CharField(max_length=20, blank=True, null=True)
    bank_branch_name = models.CharField(max_length=100, blank=True, null=True)
    bank_branch_city = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=30, blank=True, null=True)
    
    # JSON data for full response and additional information
    raw_data = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        if self.person_type == 'IranianPrivatePerson':
            return f"{self.first_name} {self.last_name} ({self.unique_identifier})"
        else:
            return f"{self.company_name} ({self.unique_identifier})"


class Shareholder(models.Model):
    """Store shareholder information for legal persons."""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shareholders')
    unique_identifier = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Shareholder"
        verbose_name_plural = "Shareholders"
        unique_together = ['profile', 'unique_identifier']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"


class ErrorLog(models.Model):
    """Store error logs from API calls."""
    error_data = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
    
    def __str__(self):
        return f"Error at {self.timestamp}"