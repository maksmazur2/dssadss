from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, logout, authenticate
from datetime import date, datetime, time
from django.db import transaction
from django.db.models import Max, Q, Sum, F
from django.db.models.functions import Coalesce
from django.views.decorators.csrf import csrf_exempt
import ast



# Utils

def purge_expired_bookings():
    """Remove bookings where the slot has fully passed."""
    today = date.today()
    now_time = datetime.now().time()
    Registration.objects.filter(
        Q(stayfrom__lt=today)
        | (Q(stayfrom=today) & Q(end_time__lte=now_time))
    ).delete()


def purge_old_pantry_data():
    """Drop pantry menus/orders that are in the past to keep inventory day-by-day."""
    today = date.today()
    Order.objects.filter(pickup_date__lt=today).delete()
    DailyMenu.objects.filter(date__lt=today).delete()


# Create your views here.

def index(request):
    purge_expired_bookings()
    regno = 1001 if Userregistration.objects.count() == 0 else Userregistration.objects.aggregate(max=Max('regNo'))[
                                                                   "max"] + 1
    error = ""
    today = date.today()
    display_date = today
    menus_qs = DailyMenu.objects.select_related('dish').filter(date=today, is_active=True)
    if not menus_qs.exists():
        next_date = (
            DailyMenu.objects.filter(date__gte=today, is_active=True)
            .order_by('date')
            .values_list('date', flat=True)
            .first()
        )
        if next_date:
            display_date = next_date
            menus_qs = DailyMenu.objects.select_related('dish').filter(date=display_date, is_active=True)
    menus = menus_qs.order_by('meal_type', 'dish__name')
    menu_grouped = {'breakfast': [], 'lunch': [], 'dinner': []}
    for m in menus:
        menu_grouped[m.meal_type].append(m)
    menu_sections = [
        ("Breakfast", menu_grouped['breakfast']),
        ("Lunch", menu_grouped['lunch']),
        ("Dinner", menu_grouped['dinner']),
    ]
    showing_today = display_date == today
    if request.method == 'POST':

        fn = request.POST['firstName']
        ln = request.POST['lastName']
        gen = request.POST['gender']
        cno = request.POST['contactNo']
        e = request.POST['email']
        pas = request.POST['password']
        im = request.FILES.get('image')

        try:
            if User.objects.filter(username=e).exists():
                error = "exists"
                return render(request, 'index.html', locals())
            user = User.objects.create_user(username=e, password=pas, first_name=fn, last_name=ln)
            Userregistration.objects.create(users=user, regNo=regno, gender=gen, contactNo=cno, image=im,
                                            regDate=date.today())
            error = "no"
        except:
            error = "yes"
    return render(request, 'index.html', locals())


def user_login(request):
    error = ""
    if request.method == 'POST':
        e = request.POST['email']
        p = request.POST['pwd']
        user = authenticate(username=e, password=p)
        try:
            if user:
                login(request, user)
                error = "no"
            else:
                error = "yes"
        except:
            error = "yes"
    return render(request, 'user_login.html', locals())


def user_home(request):
    dishes = Dish.objects.filter(is_active=True).order_by('name')[:30]
    return render(request, 'user_home.html', {
        "dishes": dishes,
    })


@csrf_exempt  # allow booking form to submit without CSRF errors on custom JS form
def book_Hostel(request):
    if not request.user.is_authenticated:
        return redirect('user_login')
    purge_expired_bookings()

    def normalize(val, default=""):
        """Return a clean single value even if query params are nested/list strings."""
        if val is None or val == "":
            return default
        current = val
        for _ in range(15):  # generous unwrap depth
            if isinstance(current, list):
                if not current:
                    return default
                current = current[0]
                continue
            if isinstance(current, tuple):
                if not current:
                    return default
                current = current[0]
                continue
            if isinstance(current, str):
                s = current.strip()
                # If string represents list/tuple, try to eval and keep unwrapping
                if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
                    try:
                        parsed = ast.literal_eval(s)
                        current = parsed
                        continue
                    except Exception:
                        pass
                # strip surrounding quotes
                if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                    s = s[1:-1]
                return s
            # fallback for any other type
            return str(current)
        return default

    def safe_date(val):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except Exception:
            return None

    def safe_time(val):
        try:
            return datetime.strptime(val, "%H:%M").time()
        except Exception:
            return None

    success = normalize(request.GET.get('success')) == '1'  # show modal after redirect

    rooms = Rooms.objects.all()
    user = User.objects.get(id=request.user.id)
    userreg = Userregistration.objects.filter(users=user).first()
    regcount = Registration.objects.filter(userreg=userreg).count() if userreg else 0

    search_date = normalize(request.GET.get('stayfrom'))
    search_start = normalize(request.GET.get('start_time'))
    search_end = normalize(request.GET.get('end_time'))
    search_date_obj = safe_date(search_date)
    search_start_obj = safe_time(search_start)
    search_end_obj = safe_time(search_end)
    search_category = normalize(request.GET.get('category'))
    search_capacity = normalize(request.GET.get('capacity'))
    search_zone = normalize(request.GET.get('zone'))
    flag_accessible = request.GET.get('accessible') == 'on'
    flag_power = request.GET.get('power') == 'on'
    flag_floor5 = request.GET.get('floor5') == 'on'
    flag_group2 = request.GET.get('group2') == 'on'
    flag_group4 = request.GET.get('group4') == 'on'
    flag_individual = request.GET.get('individual') == 'on'

    booked_room_ids = set()
    show_results = False
    filtered_rooms = Rooms.objects.all()

    if search_category and search_category != "Show All":
        filtered_rooms = filtered_rooms.filter(category__iexact=search_category.lower())
    if search_zone and search_zone != "Show All":
        filtered_rooms = filtered_rooms.filter(zone__iexact=search_zone)
    if search_capacity and search_capacity != "All Spaces (not seats)":
        if search_capacity == "1-2 People":
            filtered_rooms = filtered_rooms.filter(Q(max_capacity__lte=2) | Q(seater__lte='2'))
        elif search_capacity == "3-4 People":
            filtered_rooms = filtered_rooms.filter(max_capacity__gte=3, max_capacity__lte=4)
        elif search_capacity == "5+ People":
            filtered_rooms = filtered_rooms.filter(max_capacity__gte=5)

    if flag_accessible:
        filtered_rooms = filtered_rooms.filter(is_accessible=True)
    if flag_power:
        filtered_rooms = filtered_rooms.filter(has_power=True)
    if flag_floor5:
        filtered_rooms = filtered_rooms.filter(floor__startswith='5')
    if flag_group2:
        filtered_rooms = filtered_rooms.filter(category__iexact='group', max_capacity__lte=2)
    if flag_group4:
        filtered_rooms = filtered_rooms.filter(category__iexact='group', max_capacity__gte=2, max_capacity__lte=4)
    if flag_individual:
        filtered_rooms = filtered_rooms.filter(category__iexact='individual', max_capacity__lte=2)

    # Block late-night window 19:00-24:00 with custom message
    no_results_msg = ""
    if search_start_obj and search_end_obj:
        if search_start_obj.hour >= 19 or search_end_obj.hour > 19:
            filtered_rooms = filtered_rooms.none()
            show_results = True
            no_results_msg = "We are sorry but there are no results available for the selected date & time. Unavailable for selected time, available at other times."
        elif search_date_obj and search_start_obj < search_end_obj:
            show_results = True
            booked_room_ids = set(
                Registration.objects.filter(
                    stayfrom=search_date_obj
                ).filter(
                    Q(start_time__lt=search_end_obj) & Q(end_time__gt=search_start_obj)
                ).values_list('rooms_id', flat=True)
            )
            filtered_rooms = filtered_rooms.exclude(id__in=booked_room_ids)
    else:
        filtered_rooms = filtered_rooms.none()

    if request.method == "POST":
        rid = normalize(request.POST.get('rooms'))
        stayfrom_raw = normalize(request.POST.get('stayfrom'))
        start_time_raw = normalize(request.POST.get('start_time'))
        end_time_raw = normalize(request.POST.get('end_time'))
        stayfrom = safe_date(stayfrom_raw)
        start_time = safe_time(start_time_raw)
        end_time = safe_time(end_time_raw)

        try:
            if not userreg:
                next_reg = 1001 if Userregistration.objects.count() == 0 else Userregistration.objects.aggregate(max=Max('regNo'))["max"] + 1
                userreg = Userregistration.objects.create(users=user, regNo=next_reg, regDate=date.today())

            roomid = Rooms.objects.get(id=rid)

            if not stayfrom or not start_time or not end_time:
                error = "yes"
                return render(request, 'book_Hostel.html', locals())

            if start_time >= end_time:
                error = "yes"
                return render(request, 'book_Hostel.html', locals())

            overlap = Registration.objects.filter(
                rooms=roomid,
                stayfrom=stayfrom
            ).filter(
                Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
            ).exists()

            if overlap:
                error = "exists"
                return render(request, 'book_Hostel.html', locals())

            courseid = None

            Registration.objects.create(
                rooms=roomid,
                course=courseid,
                userreg=userreg,
                foodstatus=None,
                appointment_date=stayfrom,
                stayfrom=stayfrom,
                start_time=start_time,
                end_time=end_time,
                duration=None,
                egycontactno=None,
                guardianName=None,
                guardianRelation=None,
                guardianContactno=None,
                corresAddress=None,
                corresCIty=None,
                corresState=None,
                corresPincode=None,
                pmntAddress=None,
                pmntCity=None,
                pmnatetState=None,
                pmntPincode=None,
                postingDate=date.today(),
                updationDate=date.today()
            )
            error = "no"
            # Redirect to styled confirmation page to avoid resubmission
            return redirect('booking_redirect')
        except:
            error = "yes"
    rooms = filtered_rooms
    return render(request, 'book_Hostel.html', locals())


def booking_redirect(request):
    if not request.user.is_authenticated:
        return redirect('user_login')
    latest_booking = None
    userreg = Userregistration.objects.filter(users=request.user).first()
    if userreg:
        latest_booking = Registration.objects.filter(userreg=userreg).order_by('-postingDate', '-id').first()
    return render(request, 'booking_redirect.html', {"booking": latest_booking})


def room_Details(request):
    if not request.user.is_authenticated:
        return redirect('user_login')
    user = request.user
    userreg = Userregistration.objects.filter(users=user).first()
    roomdata = Registration.objects.filter(userreg=userreg) if userreg else Registration.objects.none()
    return render(request, 'room_Details.html', locals())

def delete_RoomDtls(request,pid):
    if not request.user.is_authenticated:
        return redirect('user_login')
    userreg = Userregistration.objects.filter(users=request.user).first()
    roomdata = Registration.objects.filter(id=pid, userreg=userreg).first()
    if request.method == "POST" and roomdata:
        roomdata.delete()
    return redirect('room_Details')


def view_RoomDtls(request, pid):
    if not request.user.is_authenticated:
        return redirect('user_login')
    roomdata = Registration.objects.get(id=pid)
    duration = int(roomdata.duration or 0)
    room_fee = int(roomdata.rooms.fees or 0)

    totalroomcost = duration * room_fee
    totalfoodcost = duration * 2000
    totalcost = totalroomcost + totalfoodcost

    return render(request, 'view_RoomDtls.html', locals())


def my_Profile(request):
    if not request.user.is_authenticated:
        return redirect('user_login')
    user = User.objects.get(id=request.user.id)
    data = Userregistration.objects.filter(users=user).first()
    return render(request, 'my_Profile.html', locals())


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('user_login')
    user = User.objects.get(id=request.user.id)
    userdata = Userregistration.objects.get(users=user)

    error = ""
    if request.method == "POST":
        rno = request.POST['regNo']
        fname = request.POST['firstName']
        lname = request.POST['lastName']
        gen = request.POST['gender']
        cno = request.POST['contactNo']
        faculty = request.POST.get('faculty')
        perm = request.POST.get('permAddress')


        userdata.regNo = rno
        userdata.users.first_name = fname
        userdata.users.last_name = lname
        userdata.gender = gen
        userdata.contactNo = cno
        userdata.faculty = faculty
        userdata.permAddress = perm

        try:
            userdata.save()
            userdata.users.save()
            error = "no"
        except:
            error = "yes"

        try:
            image = request.FILES.get('image')
            if image:
                userdata.image = image
                userdata.save()
        except:
            pass
    return render(request, 'edit_profile.html', locals())


def change_UserPassword(request):
    if not request.user.is_authenticated:
        return redirect('index')
    error = ""
    user = request.user
    if request.method == "POST":
        o = request.POST['old']
        n = request.POST['new']
        try:
            u = User.objects.get(id=request.user.id)
            if user.check_password(o):
                u.set_password(n)
                u.save()
                error = "no"
            else:
                error = 'not'
        except:
            error = "yes"
    return render(request, 'change_UserPassword.html', locals())


@csrf_exempt  # allow login without CSRF errors on this custom form
def admin_login(request):
    error = ""
    if request.method == 'POST':
        u = request.POST['uname']
        p = request.POST['pwd']
        user = authenticate(username=u, password=p)
        try:
            if user.is_staff:
                login(request, user)
                error = "no"
            else:
                error = "yes"
        except:
            error = "yes"
    return render(request, 'admin_login.html', locals())


def admin_home(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    allstudent = Registration.objects.all().count()
    allrms = Rooms.objects.all().count()
    pantry_orders = Order.objects.count()
    active_menus = DailyMenu.objects.filter(is_active=True).count()

    return render(request, 'admin_home.html', locals())


def add_Room(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    error = ""
    if request.method == "POST":
        st = request.POST['seater']
        rno = request.POST['room_no']
        fee = request.POST['fees']
        category = request.POST.get('category') or None
        zone = request.POST.get('zone') or None
        max_capacity = request.POST.get('max_capacity') or None
        floor = request.POST.get('floor') or None
        is_accessible = True if request.POST.get('is_accessible') == 'on' else False
        has_power = True if request.POST.get('has_power') == 'on' else False
        try:
            Rooms.objects.create(
                seater=st,
                room_no=rno,
                fees=fee,
                category=category.lower() if category else None,
                zone=zone,
                max_capacity=max_capacity or None,
                floor=floor,
                is_accessible=is_accessible,
                has_power=has_power
            )
            error = "no"
        except:
            error = "yes"
    return render(request, 'add_Room.html', locals())


def manage_Room(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    room = Rooms.objects.all()
    return render(request, 'manage_Room.html', locals())


def edit_Room(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    error = ""
    room = Rooms.objects.get(id=pid)
    if request.method == "POST":
        st = request.POST['seater']
        rno = request.POST['room_no']
        fee = request.POST['fees']
        category = request.POST.get('category') or None
        zone = request.POST.get('zone') or None
        max_capacity = request.POST.get('max_capacity') or None
        floor = request.POST.get('floor') or None
        is_accessible = True if request.POST.get('is_accessible') == 'on' else False
        has_power = True if request.POST.get('has_power') == 'on' else False

        room.seater = st
        room.room_no = rno
        room.fees = fee
        room.category = category.lower() if category else None
        room.zone = zone
        room.max_capacity = max_capacity or None
        room.floor = floor
        room.is_accessible = is_accessible
        room.has_power = has_power

        try:
            room.save()
            error = "no"
        except:
            error = "yes"
    return render(request, 'edit_Room.html', locals())


def delete_Room(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    room = Rooms.objects.get(id=pid)
    room.delete()
    return redirect('manage_Room')


def manage_student(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    purge_expired_bookings()
    stdata = Registration.objects.all()
    cabinet_list = Registration.objects.values_list('rooms__room_no', flat=True).distinct()
    hour_list = [f"{h:02d}" for h in range(7, 20)]
    return render(request, 'manage_student.html', {"stdata": stdata, "cabinet_list": cabinet_list, "hour_list": hour_list})

def view_RegistrationDtls(request,pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    roomdata = Registration.objects.get(id=pid)
    # Safely compute costs even when duration/foodstatus are missing
    duration_months = int(roomdata.duration) if roomdata.duration else 0
    totalroomcost = duration_months * int(roomdata.rooms.fees)
    totalfoodcost = 0
    if roomdata.foodstatus and roomdata.foodstatus != 'Without Food':
        totalfoodcost = duration_months * 2000
    totalcost = totalroomcost + totalfoodcost
    return render(request, 'view_RegistrationDtls.html', locals())


def changePassword(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    error = ""
    user = request.user
    if request.method == "POST":
        o = request.POST['oldpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if user.check_password(o):
                u.set_password(n)
                u.save()
                error = "no"
            else:
                error = 'not'
        except:
            error = "yes"
    return render(request, 'changePassword.html', locals())

def delete_StudentReg(request,pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    roomdata = Registration.objects.get(id=pid)
    # remove only the booking; keep user profile/account intact
    roomdata.delete()
    return redirect('manage_student')


def pantry_admin(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')

    purge_old_pantry_data()

    message = ""
    error = ""

    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == "dish":
            name = request.POST.get('name', '').strip()
            if not name:
                error = "Dish name is required."
            else:
                Dish.objects.create(
                    name=name,
                    description=request.POST.get('description', ''),
                    allergens=request.POST.get('allergens', ''),
                    tags=request.POST.get('tags', '')
                )
                message = "Dish added."

        if form_type == "menu":
            dish_id = request.POST.get('dish')
            meal_type = request.POST.get('meal_type')
            date_raw = request.POST.get('date')
            portions = int(request.POST.get('portions') or 0)
            try:
                dish = Dish.objects.get(id=dish_id)
                target_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
            except Exception:
                dish = None
                target_date = None

            if not dish or not target_date:
                error = "Select a dish and date."
            elif portions < 0:
                error = "Portions must be zero or more."
            else:
                menu, created = DailyMenu.objects.get_or_create(
                    dish=dish, date=target_date, meal_type=meal_type,
                    defaults={"portions_total": portions, "portions_available": portions}
                )
                if not created:
                    ordered_qty = menu.ordered_qty()
                    menu.portions_total = portions
                    menu.portions_available = max(0, portions - ordered_qty)
                    menu.is_active = portions > 0
                    menu.save()
                    message = "Menu updated."
                else:
                    message = "Menu created."
        if form_type == "delete_menu":
            menu_id = request.POST.get('menu_id')
            try:
                menu = DailyMenu.objects.get(id=menu_id)
                # remove associated orders for that menu to keep data clean
                orders_to_remove = Order.objects.filter(items__menu_item=menu).distinct()
                orders_to_remove.delete()
                menu.delete()
                message = "Menu deleted."
            except DailyMenu.DoesNotExist:
                error = "Menu not found."

    today = date.today()
    dishes = Dish.objects.filter(is_active=True).order_by('name')
    menus = (
        DailyMenu.objects.select_related('dish')
        .filter(date__gte=today)
        .annotate(ordered=Coalesce(Sum('orderitem__quantity', filter=Q(orderitem__order__status__in=['placed', 'ready', 'completed'])), 0))
        .order_by('date', 'meal_type', 'dish__name')
    )
    orders = (
        Order.objects.select_related('user')
        .prefetch_related('items__menu_item__dish')
        .filter(pickup_date=today)
        .order_by('-created_at')
    )

    return render(request, 'pantry_admin.html', {
        "dishes": dishes,
        "menus": menus,
        "orders": orders,
        "message": message,
        "error": error,
        "today": date.today(),
    })


def pantry_menu(request):
    if not request.user.is_authenticated:
        return redirect('user_login')

    purge_old_pantry_data()

    today = date.today()
    date_str = request.GET.get('date') or today.strftime("%Y-%m-%d")
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        target_date = today
        date_str = today.strftime("%Y-%m-%d")
    if target_date < today:
        target_date = today
        date_str = today.strftime("%Y-%m-%d")

    service_windows = {
        "breakfast": (time(6, 0), time(12, 0)),
        "lunch": (time(12, 0), time(14, 0)),
        "dinner": (time(14, 0), time(23, 59, 59)),
    }
    now_time = datetime.now().time()

    success = request.GET.get('success') == '1'
    error = ""

    if request.method == "POST":
        menu_id = request.POST.get('menu_id')
        qty = int(request.POST.get('quantity') or 1)

        if qty < 1:
            error = "Quantity must be at least 1."
        else:
            try:
                with transaction.atomic():
                    menu = DailyMenu.objects.select_for_update().get(id=menu_id, date=target_date, is_active=True)
                    win = service_windows.get(menu.meal_type)
                    if target_date != today:
                        error = "Ordering opens on the day of service only."
                    elif not win or not (win[0] <= now_time < win[1]):
                        error = f"{menu.get_meal_type_display()} ordering hours are {win[0].strftime('%H:%M')} - {win[1].strftime('%H:%M')}."
                    elif menu.portions_available < qty:
                        error = "Not enough portions left."
                    else:
                        order = Order.objects.create(
                            user=request.user,
                            pickup_date=menu.date,
                            meal_type=menu.meal_type
                        )
                        OrderItem.objects.create(order=order, menu_item=menu, quantity=qty)
                        menu.portions_available = menu.portions_available - qty
                        menu.is_active = menu.portions_available > 0
                        menu.save(update_fields=['portions_available', 'is_active'])
                        return redirect(f"/pantry?date={date_str}&success=1")
            except DailyMenu.DoesNotExist:
                error = "Menu item not available."

    menus_qs = DailyMenu.objects.select_related('dish').filter(date=target_date, is_active=True).order_by('meal_type', 'dish__name')
    menus = []
    for m in menus_qs:
        start, end = service_windows.get(m.meal_type, (None, None))
        m.window_label = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}" if start and end else "Unavailable"
        m.is_in_window = (target_date == today) and start and end and (start <= now_time < end)
        m.is_future_window = (target_date == today) and start and end and now_time < start
        menus.append(m)
    grouped = {'breakfast': [], 'lunch': [], 'dinner': []}
    for m in menus:
        grouped[m.meal_type].append(m)

    meal_sections = [
        ("Breakfast", grouped['breakfast']),
        ("Lunch", grouped['lunch']),
        ("Dinner", grouped['dinner']),
    ]

    my_orders = (
        Order.objects.filter(user=request.user, pickup_date=target_date)
        .prefetch_related('items__menu_item__dish')
        .order_by('-created_at')
    )

    return render(request, 'pantry_menu.html', {
        "target_date": target_date,
        "date_str": date_str,
        "menus": grouped,
        "meal_sections": meal_sections,
        "success": success,
        "error": error,
        "my_orders": my_orders,
        "service_windows": service_windows,
        "today": today,
    })


def Logout(request):
    logout(request)
    return redirect('index')
