from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Courses(models.Model):
    course_code = models.CharField(max_length=255, null=True)
    course_sn = models.CharField(max_length=100, null=True)
    course_fn = models.CharField(max_length=255, null=True)
    posting_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course_code

class Rooms(models.Model):
    seater = models.CharField(max_length=100, null=True)
    room_no = models.CharField(max_length=100, null=True)
    fees = models.CharField(max_length=255, null=True)
    category = models.CharField(max_length=50, null=True, blank=True)  # individual | group | quiet
    zone = models.CharField(max_length=100, null=True, blank=True)
    max_capacity = models.PositiveIntegerField(null=True, blank=True)
    floor = models.CharField(max_length=50, null=True, blank=True)
    is_accessible = models.BooleanField(default=False)
    has_power = models.BooleanField(default=True)
    posting_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room_no or 'Room'} ({self.seater} seaters)"

class States(models.Model):
    statename = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.statename

class Userregistration(models.Model):
    users = models.ForeignKey(User, on_delete=models.CASCADE)
    regNo = models.IntegerField(null=True)
    gender = models.CharField(max_length=50, null=True)
    contactNo = models.CharField(max_length=15, null=True)
    image = models.FileField(max_length=200, null=True)
    faculty = models.CharField(max_length=100, null=True, blank=True)
    permAddress = models.CharField(max_length=350, null=True, blank=True)
    regDate = models.DateField(null=True)
    updationDate = models.DateTimeField(auto_now_add=True)

class Registration(models.Model):
    rooms = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    foodstatus = models.CharField(max_length=100, null=True)
    stayfrom = models.DateField(null=True, blank=True)
    appointment_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration = models.CharField(max_length=50, null=True)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, null=True, blank=True)
    userreg = models.ForeignKey(Userregistration, on_delete=models.CASCADE)
    egycontactno = models.CharField(max_length=15, null=True)
    guardianName = models.CharField(max_length=250, null=True)
    guardianRelation = models.CharField(max_length=250, null=True)
    guardianContactno = models.CharField(max_length=15, null=True)
    corresAddress = models.CharField(max_length=350, null=True)
    corresCIty = models.CharField(max_length=100, null=True)
    corresState = models.CharField(max_length=100, null=True)
    corresPincode = models.CharField(max_length=50, null=True)
    pmntAddress = models.CharField(max_length=350, null=True)
    pmntCity = models.CharField(max_length=100, null=True)
    pmnatetState = models.CharField(max_length=100, null=True)
    pmntPincode = models.CharField(max_length=50, null=True)
    postingDate = models.DateField(null=True)
    updationDate = models.DateField(null=True)

MEAL_CHOICES = (
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('dinner', 'Dinner'),
)


class Dish(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    allergens = models.CharField(max_length=200, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DailyMenu(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    portions_total = models.PositiveIntegerField(default=0)
    portions_available = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('dish', 'date', 'meal_type')
        ordering = ['date', 'meal_type', 'dish__name']

    def __str__(self):
        return f"{self.dish.name} - {self.get_meal_type_display()} ({self.date})"

    @property
    def sold_out(self):
        return self.portions_available <= 0

    def ordered_qty(self):
        from django.db.models import Sum
        return self.orderitem_set.filter(order__status__in=['placed', 'ready', 'completed'])\
                   .aggregate(total=Sum('quantity')).get('total') or 0


class Order(models.Model):
    STATUS_CHOICES = (
        ('placed', 'Placed'),
        ('ready', 'Ready for pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    pickup_date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(DailyMenu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item.dish.name} x{self.quantity}"



