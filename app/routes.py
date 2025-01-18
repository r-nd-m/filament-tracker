from flask import render_template, request, redirect, url_for
from app import app, db
from app.models import FilamentRoll, PrintJob

@app.route('/')
def index():
    rolls = FilamentRoll.query.all()
    print_jobs = PrintJob.query.order_by(PrintJob.id.desc()).all()  # Show latest prints first
    return render_template('index.html', rolls=rolls, print_jobs=print_jobs)

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
    length_used = float(request.form['length_used'])
    weight_used = float(request.form['weight_used'])  # Ensure float conversion
    project_name = request.form['project_name']

    roll = FilamentRoll.query.get(filament_id)
    if roll and roll.remaining_weight >= weight_used:
        print_job = PrintJob(filament_id=filament_id, length_used=length_used, weight_used=weight_used, project_name=project_name)
        db.session.add(print_job)
        roll.remaining_weight -= weight_used
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/delete_roll/<int:roll_id>', methods=['POST'])
def delete_roll(roll_id):
    roll = FilamentRoll.query.get_or_404(roll_id)
    
    # Ensure all associated print jobs are deleted first
    PrintJob.query.filter_by(filament_id=roll.id).delete()

    db.session.delete(roll)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/delete_print/<int:print_id>', methods=['POST'])
def delete_print(print_id):
    print_job = PrintJob.query.get_or_404(print_id)

    # Restore the filament roll’s remaining weight
    filament = FilamentRoll.query.get(print_job.filament_id)
    if filament:
        filament.remaining_weight += print_job.weight_used

    db.session.delete(print_job)
    db.session.commit()
    
    return redirect(url_for('index'))