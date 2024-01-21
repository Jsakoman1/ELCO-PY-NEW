import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)



def load_data():
    with open('data.json', 'r') as file:
        data = json.load(file)

    return data

def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=2)

def update_global_data():
    global data, positions, workers, workers_by_role, schedules, roles, shifts
    data = load_data()
    positions = data.get('positions', [])
    workers = data.get('workers', [])
    workers_by_role = data.get('workers_by_role', {})
    schedules = data.get('schedules', {})
    roles = data.get('roles', [])
    shifts = data.get('shifts', [])

    

update_global_data()

def get_start_date(year, month, day):
    target_date = datetime(year, month, day)
    start_of_week = target_date - timedelta(days=target_date.weekday())
    return start_of_week.date()

def generate_week_days(start_date, week_number):
    # Generate an array of the days for the specified week number
    week_days = [start_date + timedelta(days=i + (week_number - 1) * 7) for i in range(7)]
    return week_days
 
@app.route('/create_week', methods=['POST'])
def create_week():
    data = load_data()

    entered_year = request.form.get('year')
    entered_week_number = request.form.get('week_number')

    if entered_year and entered_week_number and 2024 <= int(entered_year) <= 2100:
        # Calculate the start date of the week
        start_date = get_start_date(int(entered_year), 1, 1)
        week_start_date = generate_week_days(start_date, int(entered_week_number))[0]

        # Create entries for the week
        create_schedule_entries(week_start_date)

    return redirect(url_for('scheduler'))

@app.route('/')
def home():
    update_global_data()
    start_date = get_start_date(2024, 1, 1)  # January 1, 2024

    schedules_by_week = group_schedules_by_week(data['schedules'], start_date)

    return render_template('index.html', start_date=start_date, positions=positions, workers=workers, workers_by_role=workers_by_role, schedules_by_week=schedules_by_week)

@app.route('/positions', methods=['GET', 'POST'])
def positions_page():
    if request.method == 'POST':
        # Handle adding a new position
        new_position = request.form.get('new_position')
        if new_position:
            positions.append(new_position)
            data = load_data()
            data['positions'] = positions
            save_data(data)
            update_global_data()

        # Handle deleting a position
        deleted_position = request.form.get('position')
        if deleted_position:
            positions.remove(deleted_position)
            data = load_data()
            data['positions'] = positions

            # Remove the corresponding role when deleting a position
            if deleted_position in data['workers_by_role']:
                del data['workers_by_role'][deleted_position]

            # Remove the corresponding schedule entries for the deleted position
            for day, position_data in data['schedules'].items():
                if deleted_position in position_data:
                    del position_data[deleted_position]

            save_data(data)
            update_global_data()

        # Handle adding a new shift
        new_shift = request.form.get('new_shift')
        if new_shift:
            data = load_data()
            shifts = data.get('shifts', [])
            if new_shift not in shifts:
                shifts.append(new_shift)
                data['shifts'] = shifts
                save_data(data)

    # Reload data before rendering the positions page
    data = load_data()
    positions = data.get('positions', [])
    shifts = data.get('shifts', [])

    return render_template('positions.html', positions=positions, shifts=shifts)

@app.route('/workers', methods=['GET', 'POST'])
def workers_page():
    if request.method == 'POST':
        # Check if the form is for adding a worker to a role
        if 'worker' in request.form and 'role' in request.form:
            worker = request.form.get('worker')
            role = request.form.get('role')

            if worker and role:
                data = load_data()
                if role not in data['workers_by_role']:
                    data['workers_by_role'][role] = []

                data['workers_by_role'][role].append(worker)
                save_data(data)

            update_global_data()
            load_data()

        # Check if the form is for adding a new worker
        elif 'new_worker_name' in request.form and 'new_worker_role' in request.form:
            new_worker = request.form.get('new_worker_name')
            new_worker_role = request.form.get('new_worker_role')

            if new_worker and new_worker_role:
                workers.append(new_worker)
                data = load_data()
                data['workers'] = workers

                if new_worker_role not in data['workers_by_role']:
                    data['workers_by_role'][new_worker_role] = [new_worker]
                else:
                    data['workers_by_role'][new_worker_role].append(new_worker)
                save_data(data)

            load_data()
            update_global_data()

    workers_with_roles = {}
    for role, workers_in_role in workers_by_role.items():
        for worker in workers_in_role:
            if worker not in workers_with_roles:
                workers_with_roles[worker] = [role]
            else:
                workers_with_roles[worker].append(role)

    update_global_data()
    load_data()
    return render_template('workers.html', workers=workers, workers_by_role=workers_by_role, workers_with_roles=workers_with_roles)

@app.route('/delete_worker', methods=['POST'])
def delete_worker():
    if request.method == 'POST':
        worker_to_delete = request.form.get('worker')

        if worker_to_delete:
            data = load_data()

            # Remove the worker from the main list
            if worker_to_delete in data['workers']:
                data['workers'].remove(worker_to_delete)

            # Remove the worker from each role in the workers_by_role dictionary
            for role, workers_in_role in data['workers_by_role'].items():
                if worker_to_delete in workers_in_role:
                    workers_in_role.remove(worker_to_delete)

            save_data(data)

    update_global_data()

    return redirect(url_for('workers_page'))

@app.route('/add_worker_to_role', methods=['POST'])
def add_worker_to_role():
    if request.method == 'POST':
        worker = request.form.get('worker')
        role = request.form.get('role')

        if worker and role:
            
            data = load_data()
            if role not in data['workers_by_role']:
                data['workers_by_role'][role] = []

            data['workers_by_role'][role].append(worker)
            save_data(data)

        update_global_data()  

    
    return redirect(url_for('workers_page'))

@app.route('/add_new_role', methods=['POST'])
def add_new_role():
    if request.method == 'POST':
        new_role = request.form.get('new_role')

        if new_role:
            # Update the workers_by_role data
            data = load_data()
            data['workers_by_role'][new_role] = []  # Initialize with an empty list of workers

            # Update the roles data
            roles = data.get('roles', [])
            if new_role not in roles:
                roles.append(new_role)
                data['roles'] = roles

            save_data(data)

    # Reload data before rendering workers page
    data = load_data()
    workers_by_role = data.get('workers_by_role', {})

    # Redirect back to the workers page after adding a new role
    return render_template('workers.html', workers=workers, workers_by_role=workers_by_role)

@app.route('/delete_role', methods=['POST'])
def delete_role():
    if request.method == 'POST':
        role_to_delete = request.form.get('role')

        if role_to_delete:
            data = load_data()
            if role_to_delete in data['workers_by_role']:
                del data['workers_by_role'][role_to_delete]

                # Update the roles data
                roles = data.get('roles', [])
                if role_to_delete in roles:
                    roles.remove(role_to_delete)
                    data['roles'] = roles

                save_data(data)

    # Reload data before rendering the roles page
    data = load_data()
    workers_by_role = data.get('workers_by_role', {})

    # Redirect back to the roles page after deleting a role
    return render_template('workers.html', workers=workers, workers_by_role=workers_by_role)

@app.route('/add_new_shift', methods=['POST'])
def add_new_shift():
    if request.method == 'POST':
        new_shift = request.form.get('new_shift')

        if new_shift:
            # Update the shifts data
            data = load_data()
            shifts = data.get('shifts', [])

            if new_shift not in shifts:
                shifts.append(new_shift)
                data['shifts'] = shifts

                save_data(data)

    # Reload data before rendering positions page
    data = load_data()
    shifts = data.get('shifts', [])

    # Redirect back to the positions page after adding a new shift
    return render_template('positions.html', positions=positions, shifts=shifts)

@app.route('/delete_shift', methods=['POST'])
def delete_shift():
    if request.method == 'POST':
        shift_to_delete = request.form.get('shift')

        if shift_to_delete:
            data = load_data()
            shifts = data.get('shifts', [])

            if shift_to_delete in shifts:
                shifts.remove(shift_to_delete)
                data['shifts'] = shifts

                save_data(data)

    # Reload data before rendering the positions page
    data = load_data()
    positions = data.get('positions', [])
    shifts = data.get('shifts', [])

    # Redirect back to the positions page after deleting a shift
    return render_template('positions.html', positions=positions, shifts=shifts)

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    if request.method == 'POST':
        # Load existing data from the file
        data = load_data()

        # Get the schedule data from the request
        schedule_data = request.json

        # Update the schedules dictionary with the new data
        for day, positions in schedule_data.items():
            if day not in data['schedules']:
                data['schedules'][day] = {}
            
            for position, worker in positions.items():
                data['schedules'][day][position] = worker

        # Save the updated data to the file
        save_data(data)

        return 'Schedule saved successfully', 200

@app.route('/schedules')
def schedules():
    update_global_data()
    start_date = get_start_date(2024, 1, 1)  # January 1, 2024
    week_1_days = generate_week_days(start_date, week_number=1)
    week_2_days = generate_week_days(start_date, week_number=2)

    # Create a schedule for each position for week 1
    schedule_week_1 = {position: {day: None for day in week_1_days} for position in positions}
    schedule_week_2 = {position: {day: None for day in week_2_days} for position in positions}

    return render_template('schedules.html', start_date=start_date, positions=positions, workers=workers, workers_by_role=workers_by_role, week_1_days=week_1_days, week_2_days=week_2_days, schedules=data['schedules'], schedule_week_1=schedule_week_1, schedule_week_2=schedule_week_2, checkbox={'checked': False})

@app.route('/settings')
def settings():
    start_date = get_start_date(2024, 1, 1)  # January 1, 2024
    current_date = datetime.now().strftime("%Y-%m-%d")  # Format as YYYY-MM-DD

    return render_template('settings.html', start_date=start_date, current_date=current_date)

@app.route('/scheduler', methods=['GET', 'POST'])
def scheduler():
    start_date = get_start_date(2024, 1, 1)  # January 1, 2024
    current_date = datetime.now().strftime("%Y-%m-%d")  # Format as YYYY-MM-DD
    current_year = datetime.now().year
    schedules_by_week = group_schedules_by_week(load_data()['schedules'], start_date)

    update_global_data()

    existing_years = get_existing_years()

    if request.method == 'POST':
        if 'year' in request.form:
            entered_year = request.form.get('year')

            if entered_year and 2024 <= int(entered_year) <= 2100:
                existing_years = get_existing_years()

    return render_template('scheduler.html', start_date=start_date, current_date=current_date, current_year=current_year,
                           schedules_by_week=schedules_by_week, positions=positions, shifts=shifts, roles=roles)

@app.route('/week_details/<int:week_number>', methods=['GET', 'POST'])
def week_details(week_number):
    update_global_data()
    start_date = get_start_date(2024, 1, 1)  # January 1, 2024
    week_days = generate_week_days(start_date, week_number=week_number)

    # Get positions and workers from global data
    positions = data.get('positions', [])
    workers = data.get('workers', [])

    # Create a schedule for each position for the specified week
    schedule_week = {position: {day: None for day in week_days} for position in positions}

    # Create a list of dictionaries containing date, schedule, and dropdown data
    week_data = [{'date': day, 'schedule': schedule_week, 'dropdown_data': {'positions': positions, 'workers': workers}} for day in week_days]

    return render_template('week_details.html', start_date=start_date, positions=positions, workers=workers,
                           workers_by_role=workers_by_role, week_days=week_days, schedules=data['schedules'],
                           schedule_week=schedule_week, checkbox={'checked': False}, week_data=week_data)






def create_schedule_entries(start_date=None):
    data = load_data()

    # If start_date is not provided, default to the current date
    if start_date is None:
        start_date = datetime.now().date()

    # Ensure that the start_date is a Monday
    if start_date.weekday() != 0:
        # Find the Monday before the selected date
        start_date = start_date - timedelta(days=start_date.weekday())

    # Create entries for the next seven days
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        formatted_date = current_date.strftime("%Y-%m-%d")

        # Check if the date already exists in schedules
        if formatted_date not in data['schedules']:
            # Create a schedule for each position for the formatted date
            schedule_for_day = {position: None for position in data['positions']}
            data['schedules'][formatted_date] = schedule_for_day

    # Save the updated data to the file
    save_data(data)

def get_existing_years():
    data = load_data()
    existing_years = set()

    for date_str in data['schedules'].keys():
        year = datetime.strptime(date_str, "%Y-%m-%d").year
        existing_years.add(year)

    return existing_years

def group_schedules_by_week(schedules, start_date):
    schedules_by_week = {}

    for date_str, schedule_data in schedules.items():
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        week_number = (date - start_date).days // 7 + 1

        if week_number not in schedules_by_week:
            schedules_by_week[week_number] = []

        schedules_by_week[week_number].append({'date': date_str, 'schedule': schedule_data})

    return schedules_by_week

@app.route('/clear_all_schedules', methods=['POST'])
def clear_all_schedules():
    data = load_data()

    # Clear all schedules
    data['schedules'] = {}

    # Save the updated data to the file
    save_data(data)

    # Redirect back to the scheduler page or any other appropriate page
    return redirect(url_for('scheduler'))


if __name__ == "__main__":
    app.run(debug=True)