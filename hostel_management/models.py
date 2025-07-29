# from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

# User Types
USER_TYPES = [
    ('student', 'Student'),
    ('staff', 'Hostel Staff'),
    ('provost', 'Provost/Warden'),
    ('admin', 'System Admin'),
]

# Room Types
ROOM_TYPES = [
    ('single', 'Single'),
    ('double', 'Double'),
    ('shared', 'Shared'),
]

# Application Status
APPLICATION_STATUS = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('allocated', 'Allocated'),
]

# Complaint Categories
COMPLAINT_CATEGORIES = [
    ('maintenance', 'Maintenance'),
    ('security', 'Security'),
    ('facilities', 'Facilities'),
    ('cleanliness', 'Cleanliness'),
    ('noise', 'Noise'),
    ('other', 'Other'),
]

# Complaint Status
COMPLAINT_STATUS = [
    ('submitted', 'Submitted'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
]

# Notice Categories
NOTICE_CATEGORIES = [
    ('general', 'General'),
    ('important', 'Important'),
    ('urgent', 'Urgent'),
    ('academic', 'Academic'),
    ('maintenance', 'Maintenance'),
]

# Priority Levels
PRIORITY_LEVELS = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
]

class CustomUser(AbstractUser):
    """Extended User model with hostel-specific fields"""
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

class StudentProfile(models.Model):
    """Student-specific profile information"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    academic_year = models.PositiveIntegerField()
    semester = models.PositiveIntegerField(default=1)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"
    
    class Meta:
        ordering = ['student_id']

class Room(models.Model):
    """Room inventory management"""
    room_number = models.CharField(max_length=10, unique=True)
    floor = models.PositiveIntegerField()
    block = models.CharField(max_length=10, default='A')
    capacity = models.PositiveIntegerField(default=2)
    current_occupancy = models.PositiveIntegerField(default=0)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='double')
    has_attached_bathroom = models.BooleanField(default=True)
    has_air_conditioning = models.BooleanField(default=False)
    has_furniture = models.BooleanField(default=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    maintenance_status = models.CharField(max_length=50, default='good')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Room {self.room_number} - {self.get_room_type_display()}"
    
    @property
    def is_full(self):
        return self.current_occupancy >= self.capacity
    
    @property
    def available_beds(self):
        return self.capacity - self.current_occupancy
    
    class Meta:
        ordering = ['room_number']

class RoomApplication(models.Model):
    """Room allocation applications"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='room_applications')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='applications')
    application_date = models.DateTimeField(auto_now_add=True)
    preferred_move_date = models.DateField()
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    priority_score = models.PositiveIntegerField(default=0)
    reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_applications')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.room.room_number} ({self.status})"
    
    class Meta:
        ordering = ['-application_date']
        unique_together = ['student', 'room', 'status']

class RoomAllocation(models.Model):
    """Current room allocations"""
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='current_allocation')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='current_residents')
    allocated_date = models.DateTimeField(auto_now_add=True)
    allocated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='allocated_rooms')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.student.student_id} in {self.room.room_number}"
    
    class Meta:
        ordering = ['-allocated_date']

class Complaint(models.Model):
    """Complaint management system"""
    complaint_id = models.CharField(max_length=20, unique=True, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=20, choices=COMPLAINT_CATEGORIES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=COMPLAINT_STATUS, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to='complaints/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.complaint_id:
            # Generate complaint ID: CMP-YYYYMMDD-XXXX
            from django.db.models import Max
            today = timezone.now().strftime('%Y%m%d')
            last_complaint = Complaint.objects.filter(
                complaint_id__startswith=f'CMP-{today}'
            ).aggregate(Max('id'))
            
            if last_complaint['id__max']:
                sequence = last_complaint['id__max'] + 1
            else:
                sequence = 1
            
            self.complaint_id = f'CMP-{today}-{sequence:04d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.complaint_id} - {self.subject}"
    
    class Meta:
        ordering = ['-submitted_at']

class Notice(models.Model):
    """Notice board system"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=NOTICE_CATEGORIES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    target_audience = models.CharField(max_length=50, default='all')  # all, specific_block, specific_floor
    
    def __str__(self):
        return f"{self.title} - {self.get_category_display()}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        # Set default expiry date if not provided
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']

class NoticeAttachment(models.Model):
    """Notice file attachments"""
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='notices/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notice.title} - {self.filename}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)

# Additional models for Phase 2 features (basic structure)

class StipendTransaction(models.Model):
    """Stipend management system"""
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='stipend_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    reference_number = models.CharField(max_length=50, unique=True)
    processed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='processed_stipends')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.student.student_id} - ${self.amount} - {self.transaction_date.date()}"
    
    class Meta:
        ordering = ['-transaction_date']

class LostItem(models.Model):
    """Lost and found system"""
    ITEM_CATEGORIES = [
        ('electronics', 'Electronics'),
        ('books', 'Books'),
        ('clothing', 'Clothing'),
        ('documents', 'Documents'),
        ('accessories', 'Accessories'),
        ('other', 'Other'),
    ]
    
    ITEM_STATUS = [
        ('lost', 'Lost'),
        ('found', 'Found'),
        ('claimed', 'Claimed'),
        ('expired', 'Expired'),
    ]
    
    reporter = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='lost_items')
    item_name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=ITEM_CATEGORIES)
    lost_location = models.CharField(max_length=100)
    lost_date = models.DateTimeField()
    contact_info = models.CharField(max_length=100)
    image = models.ImageField(upload_to='lost_items/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=ITEM_STATUS, default='lost')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
