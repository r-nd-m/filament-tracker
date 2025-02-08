from datetime import datetime
from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from app.models import FilamentRoll, PrintJob, TempPrintJob

@app.route('/')
def index():
    rolls = FilamentRoll.query.all()
    print_jobs = PrintJob.query.order_by(PrintJob.date.desc()).all()
    temp_jobs = TempPrintJob.query.order_by(TempPrintJob.date.desc()).all()
    return render_template('index.html', rolls=rolls, print_jobs=print_jobs, datetime=datetime,  temp_jobs=temp_jobs)

@app.route('/add_roll', methods=['POST'])
def add_roll():
    maker = request.form['maker']
    color = request.form['color']
    total_weight = float(request.form['total_weight'])
    remaining_weight = float(request.form['remaining_weight'])

    roll = FilamentRoll(maker=maker, color=color, total_weight=total_weight, remaining_weight=remaining_weight, in_use=True)
    db.session.add(roll)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/add_print', methods=['POST'])
def add_print():
    filament_id = int(request.form['filament_id'])
    weight_used = float(request.form['weight_used'])
    project_name = request.form['project_name']
    
    # Parse date from input, fallback to current time
    date_str = request.form['date']
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M") if date_str else datetime.now()

    print_job = PrintJob(
        filament_id=filament_id,
        weight_used=weight_used,
        project_name=project_name,
        date=date  # Ensure local time is stored
    )

    filament = db.session.get(FilamentRoll, filament_id)
    if filament:
        filament.remaining_weight -= weight_used

    db.session.add(print_job)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/delete_roll/<int:roll_id>', methods=['POST'])
def delete_roll(roll_id):
    roll = db.session.get(FilamentRoll, roll_id)
    
    # Ensure all associated print jobs are deleted first
    PrintJob.query.filter_by(filament_id=roll.id).delete()

    db.session.delete(roll)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/delete_print/<int:print_id>', methods=['POST'])
def delete_print(print_id):
    print_job = db.session.get(PrintJob, print_id)

    # Restore the filament roll’s remaining weight
    filament = db.session.get(FilamentRoll, print_job.filament_id)
    if filament:
        filament.remaining_weight += print_job.weight_used

    db.session.delete(print_job)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/edit_roll/<int:roll_id>', methods=['POST'])
def edit_roll(roll_id):
    roll = db.session.get(FilamentRoll, roll_id)

    roll.maker = request.form['maker']
    roll.color = request.form['color']
    roll.total_weight = float(request.form['total_weight'])
    roll.remaining_weight = float(request.form['remaining_weight'])
    roll.in_use = 'in_use' in request.form  # Checkbox handling

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_print/<int:print_id>', methods=['POST'])
def edit_print(print_id):
    print_job = db.session.get(PrintJob, print_id)
    filament = db.session.get(FilamentRoll, print_job.filament_id)

    if filament:
        filament.remaining_weight += print_job.weight_used

    print_job.project_name = request.form['project_name']
    print_job.weight_used = float(request.form['weight_used'])
    print_job.filament_id = int(request.form['filament_id'])

    # Parse new date from input
    date_str = request.form['date']
    print_job.date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M") if date_str else datetime.now()

    new_filament = db.session.get(FilamentRoll, print_job.filament_id)
    if new_filament:
        new_filament.remaining_weight -= print_job.weight_used

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/duplicate_roll/<int:roll_id>', methods=['POST'])
def duplicate_roll(roll_id):
    roll = db.session.get(FilamentRoll, roll_id)
    if not roll:
        return "Error: Filament roll not found.", 400

    # Capture new values from the form
    new_maker = request.form['maker']
    new_color = request.form['color']
    new_total_weight = float(request.form['total_weight'])
    new_remaining_weight = float(request.form['remaining_weight'])
    new_in_use = 'in_use' in request.form  # Checkbox handling

    # Create a new roll with modified values
    new_roll = FilamentRoll(
        maker=new_maker,
        color=new_color,
        total_weight=new_total_weight,
        remaining_weight=new_remaining_weight,
        in_use=new_in_use
    )
    db.session.add(new_roll)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/duplicate_print/<int:print_id>', methods=['POST'])
def duplicate_print(print_id):
    print = db.session.get(FilamentRoll, print_id)
    if not print:
        return "Error: Filament roll not found.", 400
    
    new_project_name = request.form['project_name']
    new_weight_used = float(request.form['weight_used'])
    new_filament_id = int(request.form['filament_id'])

    # Parse new date or use current time
    date_str = request.form['date']
    new_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M") if date_str else datetime.now()

    new_print_job = PrintJob(
        filament_id=new_filament_id,
        weight_used=new_weight_used,
        project_name=new_project_name,
        date=new_date
    )

    new_filament = db.session.get(FilamentRoll, new_filament_id)
    if new_filament:
        new_filament.remaining_weight -= new_weight_used

    db.session.add(new_print_job)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/add_temp_job', methods=['POST'])
def add_temp_job():
    data = request.get_json()

    # Validate incoming data
    if not data or "project_name" not in data or "weight_used" not in data:
        return jsonify({"error": "Invalid data"}), 400

    try:
        # Handle missing or incorrect date format
        date_str = data.get("date", "")
        try:
            job_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M") if date_str else datetime.now()
        except ValueError:
            job_date = datetime.now()  # Use current time if format is invalid

        # Create the temporary job
        temp_job = TempPrintJob(
            project_name=data["project_name"],
            weight_used=data["weight_used"],
            date=job_date
        )

        db.session.add(temp_job)
        db.session.commit()

        return jsonify({"message": "Temporary job added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_temp_job/<int:job_id>', methods=['POST'])
def delete_temp_job(job_id):
    job = db.session.get(TempPrintJob, job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/approve_temp_job/<int:job_id>', methods=['POST'])
def approve_temp_job(job_id):
    job = db.session.get(TempPrintJob, job_id)

    # Get form data
    project_name = request.form.get("project_name")
    date = request.form.get("date")
    weight_used = request.form.get("weight_used")
    filament_id = request.form.get("filament_id")

    # Convert date from string to datetime
    try:
        job_date = datetime.strptime(date, "%Y-%m-%dT%H:%M")
    except ValueError:
        job_date = datetime.now()  # Default to current time if invalid

    # Move job to PrintJob table
    new_print = PrintJob(
        project_name=project_name,
        date=job_date,
        weight_used=weight_used,
        filament_id=filament_id
    )

    db.session.add(new_print)
    db.session.delete(job)  # Remove from temp jobs
    db.session.commit()

    return redirect(url_for('index'))
