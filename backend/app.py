import os, json, smtplib, ssl, threading, csv, io
from collections import defaultdict
from datetime import timedelta
from zoneinfo import ZoneInfo
import re
from datetime import datetime, timezone
from email.message import EmailMessage
from functools import wraps
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from dotenv import load_dotenv

load_dotenv(override=True)
app=Flask(__name__)
app.config['SECRET_KEY']=os.getenv('SECRET_KEY','dev-only-change-this')
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(os.path.dirname(__file__),'directory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
CORS(app, resources={r'/api/*':{'origins':os.getenv('FRONTEND_ORIGIN','http://localhost:5173')}})
db=SQLAlchemy(app)
signer=URLSafeTimedSerializer(app.config['SECRET_KEY'])

class User(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 name=db.Column(db.String(120),nullable=False)
 email=db.Column(db.String(200),unique=True,nullable=False)
 password=db.Column(db.String(255),nullable=False)
 role=db.Column(db.String(20),nullable=False)
 department=db.Column(db.String(100))
 active=db.Column(db.Boolean,default=True)
 def public(self): return dict(id=self.id,name=self.name,email=self.email,role=self.role,department=self.department,active=self.active)
class Contact(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 name=db.Column(db.String(120),nullable=False)
 unit=db.Column(db.String(100),nullable=False)
 department=db.Column(db.String(100),nullable=False)
 extension=db.Column(db.String(30),nullable=False)
 designation=db.Column(db.String(120),default='')
 phone=db.Column(db.String(50),default='')
 def public(self): return {k:getattr(self,k) for k in ('id','name','unit','department','extension','designation','phone')}
class MonthlyReportDelivery(db.Model):
 month=db.Column(db.String(7),primary_key=True)
 sent_at=db.Column(db.DateTime)
 recipients=db.Column(db.Text)
 status=db.Column(db.String(20),default='pending')

class Setting(db.Model):
 key=db.Column(db.String(60),primary_key=True)
 value=db.Column(db.Text,nullable=False)
class Audit(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 time=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
 actor_id=db.Column(db.Integer)
 actor_role=db.Column(db.String(20),default='admin')
 actor_name=db.Column(db.String(120))
 actor_email=db.Column(db.String(200))
 department=db.Column(db.String(100))
 action=db.Column(db.String(30))
 before=db.Column(db.Text)
 after=db.Column(db.Text)
 email_status=db.Column(db.String(40),default='not_required')
 def public(self):return dict(id=self.id,time=self.time.isoformat(),actor_name=self.actor_name,actor_email=self.actor_email,department=self.department,action=self.action,before=json.loads(self.before) if self.before else None,after=json.loads(self.after) if self.after else None,email_status=self.email_status)

def hash_password(password):
 return generate_password_hash(password,method='pbkdf2:sha256:600000')

def setting(k,default=''):
 s=db.session.get(Setting,k)
 return s.value if s else default

def auth(*roles):
 def decorate(fn):
  @wraps(fn)
  def wrapped(*args,**kwargs):
   token=request.headers.get('Authorization','').removeprefix('Bearer ').strip()
   try: uid=signer.loads(token,max_age=60*60*12)
   except (BadSignature,SignatureExpired): return jsonify(error='Authentication required'),401
   user=db.session.get(User,uid)
   if not user or not user.active:return jsonify(error='Account inactive'),401
   if roles and user.role not in roles:return jsonify(error='Forbidden'),403
   return fn(user,*args,**kwargs)
  return wrapped
 return decorate

def permitted(user,dept):return user.role=='super_admin' or user.department==dept

def readable_contact(raw):
    """Convert stored JSON snapshots to readable label: value lines."""
    if not raw:
        return 'None'
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return str(raw)
    if not isinstance(data, dict):
        return str(data)
    labels = {
        'name': 'Name', 'unit': 'Unit', 'department': 'Department',
        'extension': 'Extension', 'designation': 'Designation',
        'phone': 'Phone', 'id': 'Record ID'
    }
    keys = ['name', 'unit', 'department', 'extension', 'designation', 'phone', 'id']
    return '\n'.join(f'{labels[k]}: {data.get(k) or "—"}' for k in keys if k in data)


def notify(audit_id):
    """Notify active super admins of department-admin contact changes."""
    with app.app_context():
        record = db.session.get(Audit, audit_id)
        if record is None:
            return

        sender = os.getenv('SMTP_USER', '').strip()
        password = os.getenv('SMTP_APP_PASSWORD', '').replace(' ', '').strip()
        recipients = sorted({
            u.email.strip() for u in User.query.filter_by(
                role='super_admin', active=True
            ).all() if u.email and u.email.strip()
        })

        if not sender or not password or not recipients:
            record.email_status = 'not_configured'
            db.session.commit()
            return

        msg = EmailMessage()
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = (
            f'TELEPHONE | {record.department} | '
            f'Contact {record.action.upper()} | {record.actor_email}'
        )
        msg.set_content(
            f'Administrator: {record.actor_name}\n'
            f'Administrator Email: {record.actor_email}\n'
            f'Department: {record.department}\n'
            f'Action: {record.action.capitalize()}\n'
            f'Date and Time (UTC): {record.time.isoformat()}\n\n'
            f'Previous Contact Details\n'
            f'------------------------\n'
            f'{readable_contact(record.before)}\n\n'
            f'Updated Contact Details\n'
            f'-----------------------\n'
            f'{readable_contact(record.after)}\n'
        )

        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                smtp.login(sender, password)
                smtp.send_message(msg)
            record.email_status = 'sent'
        except Exception as exc:
            # Audit.email_status is limited to 40 characters in the existing schema.
            record.email_status = ('failed: ' + str(exc))[:40]
            app.logger.exception('Notification failed for audit %s', audit_id)
        finally:
            db.session.commit()

def audit(user,action,before,after,department):
 a=Audit(actor_role=user.role,actor_id=user.id,actor_name=user.name,actor_email=user.email,department=department,action=action,before=json.dumps(before),after=json.dumps(after),email_status='pending' if user.role=='admin' else 'not_required')
 db.session.add(a);db.session.commit()
 if user.role=='admin':threading.Thread(target=notify,args=(a.id,),daemon=True).start()

@app.get('/api/public/settings')
def public_settings():
    result = {k: setting(k, v) for k, v in {
        'factory_name': 'YOUR FACTORY NAME', 'subtitle': 'Internal Telephone Directory',
        'logo': '', 'theme': 'light', 'font': 'Roboto', 'palette': 'slate',
        'font_size': 'jumbo', 'layout_size': 'jumbo', 'intercom_prefix': '0442652'
    }.items()}
    try:
        result['ui_text'] = json.loads(setting('ui_text', '{}'))
    except (ValueError, TypeError):
        result['ui_text'] = {}
    return jsonify(result)
@app.get('/api/contacts')
def contacts():
 q=Contact.query
 for field in ('name','unit','department','extension'):
  val=request.args.get(field,'').strip()
  if val:q=q.filter(getattr(Contact,field).ilike(f'%{val}%'))
 return jsonify([c.public() for c in q.order_by(Contact.name).limit(500).all()])
@app.post('/api/login')
def login():
 d=request.get_json(silent=True) or {};u=User.query.filter_by(email=str(d.get('email','')).lower().strip()).first()
 if not u or not u.active or not check_password_hash(u.password,d.get('password','')):return jsonify(error='Invalid credentials'),401
 return jsonify(token=signer.dumps(u.id),user=u.public())
@app.get('/api/me')
@auth()
def me(user):return jsonify(user.public())
@app.route('/api/manage/contacts',methods=['GET','POST'])
@auth('super_admin','admin')
def manage_contacts(user):
 if request.method=='GET':
  q=Contact.query if user.role=='super_admin' else Contact.query.filter_by(department=user.department)
  return jsonify([c.public() for c in q.order_by(Contact.name).all()])
 d=request.get_json(silent=True) or {}
 if not all(str(d.get(k,'')).strip() for k in ('name','unit','department','extension')):return jsonify(error='Name, unit, department and extension required'),400
 if not permitted(user,d['department']):return jsonify(error='Department restricted'),403
 c=Contact(**{k:str(d.get(k,'')).strip() for k in ('name','unit','department','extension','designation','phone')});db.session.add(c);db.session.commit();audit(user,'created',None,c.public(),c.department)
 return jsonify(c.public()),201
@app.route('/api/manage/contacts/<int:cid>',methods=['PUT','DELETE'])
@auth('super_admin','admin')
def manage_contact(user,cid):
 c=db.get_or_404(Contact,cid)
 if not permitted(user,c.department):return jsonify(error='Department restricted'),403
 before=c.public()
 if request.method=='DELETE':
  db.session.delete(c);db.session.commit();audit(user,'deleted',before,None,before['department']);return jsonify(ok=True)
 d=request.get_json(silent=True) or {}
 if not all(str(d.get(k,'')).strip() for k in ('name','unit','department','extension')):return jsonify(error='Required fields missing'),400
 if not permitted(user,d['department']):return jsonify(error='Department restricted'),403
 for k in ('name','unit','department','extension','designation','phone'):setattr(c,k,str(d.get(k,'')).strip())
 db.session.commit();audit(user,'updated',before,c.public(),c.department);return jsonify(c.public())
@app.route('/api/users', methods=['GET', 'POST'])
@auth('super_admin')
def users(user):
    if request.method == 'GET':
        return jsonify([u.public() for u in User.query.order_by(User.name).all()])

    d = request.get_json(silent=True) or {}
    role = str(d.get('role', 'user')).strip()
    name = str(d.get('name', '')).strip()
    email = str(d.get('email', '')).strip().lower()
    password = str(d.get('password', ''))
    department = str(d.get('department') or '').strip()
    if role not in ('super_admin', 'admin', 'user'):
        return jsonify(error='Invalid role'), 400
    if not name or not email or '@' not in email or len(password) < 10:
        return jsonify(error='Name, valid email and password (10+ characters) required'), 400
    if role != 'super_admin' and not department:
        return jsonify(error='Department is required for this role'), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error='Email already exists'), 409
    u = User(name=name, email=email, password=hash_password(password),
             role=role, department=None if role == 'super_admin' else department,
             active=True)
    db.session.add(u)
    db.session.commit()
    return jsonify(u.public()), 201


@app.route('/api/users/<int:uid>', methods=['PUT', 'DELETE'])
@auth('super_admin')
def edit_user(user, uid):
    u = db.get_or_404(User, uid)
    if u.id == user.id:
        return jsonify(error='You cannot modify or delete your own account here'), 403

    # Never allow an operation that removes the final active super admin.
    active_super_admins = User.query.filter_by(role='super_admin', active=True).count()
    if request.method == 'DELETE':
        if u.role == 'super_admin' and u.active and active_super_admins <= 1:
            return jsonify(error='Cannot delete the last active super admin'), 409
        db.session.delete(u)
        db.session.commit()
        return jsonify(ok=True)

    d = request.get_json(silent=True) or {}
    role = str(d.get('role', u.role)).strip()
    department = str(d.get('department', u.department) or '').strip()
    name = str(d.get('name', u.name)).strip()
    email = str(d.get('email', u.email)).strip().lower()
    active = d.get('active', u.active)
    if not isinstance(active, bool):
        return jsonify(error='Active must be true or false'), 400
    if role not in ('super_admin', 'admin', 'user'):
        return jsonify(error='Invalid role'), 400
    if not name or not email or '@' not in email:
        return jsonify(error='Name and valid email required'), 400
    if role != 'super_admin' and not department:
        return jsonify(error='Department is required for this role'), 400
    if User.query.filter(User.email == email, User.id != u.id).first():
        return jsonify(error='Email already exists'), 409
    if u.role == 'super_admin' and u.active and (role != 'super_admin' or not active) and active_super_admins <= 1:
        return jsonify(error='Cannot remove the last active super admin'), 409
    password = d.get('password')
    if password:
        if not isinstance(password, str) or len(password) < 10:
            return jsonify(error='Password must have 10+ characters'), 400
        u.password = hash_password(password)
    u.name = name
    u.email = email
    u.role = role
    u.department = None if role == 'super_admin' else department
    u.active = active
    db.session.commit()
    return jsonify(u.public())

@app.route('/api/settings',methods=['GET','PUT'])
@auth('super_admin')
def settings(user):
 if request.method=='GET':return public_settings()
 d=request.get_json(silent=True) or {}
 for k in ('factory_name','subtitle','logo','theme','font','palette','font_size','layout_size','intercom_prefix'):
  if k in d:
   value=str(d[k])[:350000] if k=='logo' else str(d[k])[:500]
   if k=='logo' and value and not (value.startswith('https://') or value.startswith('data:image/')):return jsonify(error='Logo must be HTTPS URL or image data'),400
   if k in ('font_size','layout_size') and value not in ('normal','large','jumbo','extra_jumbo','giant'):return jsonify(error='Invalid display size'),400
   if k=='intercom_prefix' and (not value.isdigit() or len(value)>15):return jsonify(error='Intercom prefix must contain 1–15 digits'),400
   s=db.session.get(Setting,k)
   if s:s.value=value
   else:db.session.add(Setting(key=k,value=value))
 if 'ui_text' in d:
  if not isinstance(d['ui_text'], dict):return jsonify(error='Interface text must be a dictionary'),400
  if len(d['ui_text'])>300:return jsonify(error='Too many text fields'),400
  cleaned={str(k):str(v)[:300] for k,v in d['ui_text'].items() if re.fullmatch(r'(ui|placeholder)_\d{3}',str(k))}
  stored=db.session.get(Setting,'ui_text')
  if stored:stored.value=json.dumps(cleaned,ensure_ascii=False)
  else:db.session.add(Setting(key='ui_text',value=json.dumps(cleaned,ensure_ascii=False)))
 db.session.commit();return public_settings()
@app.get('/api/audit')
@auth('super_admin')
def history(user):return jsonify([a.public() for a in Audit.query.order_by(Audit.id.desc()).limit(300).all()])


# Reporting uses local India dates, while the existing audit timestamps are stored as UTC.
REPORT_TZ=ZoneInfo('Asia/Kolkata')
ACTION_NAMES={'created':'additions','updated':'updates','deleted':'deletions'}

def admin_audits(department=None, start=None, end=None):
    q=Audit.query.filter(Audit.action.in_(tuple(ACTION_NAMES)),Audit.actor_role=='admin')
    if department:q=q.filter(Audit.department==department)
    if start:q=q.filter(Audit.time>=start)
    if end:q=q.filter(Audit.time<end)
    return q.order_by(Audit.time.asc(),Audit.id.asc()).all()

def report_time(a):
    dt=a.time
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(REPORT_TZ)

def month_range(month):
    try:
        year,mon=map(int,month.split('-'))
        if not 1<=year<=9999 or not 1<=mon<=12:raise ValueError()
        start=datetime(year,mon,1,tzinfo=REPORT_TZ)
        stop=datetime(year+1,1,1,tzinfo=REPORT_TZ) if mon==12 else datetime(year,mon+1,1,tzinfo=REPORT_TZ)
        return start.astimezone(timezone.utc).replace(tzinfo=None),stop.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError,TypeError):raise ValueError('Month must be YYYY-MM')

def summarise(records):
    def blank():return {'additions':0,'updates':0,'deletions':0,'total':0}
    totals=blank();groups={k:defaultdict(blank) for k in ('day','week','month','department','admin')}
    for a in records:
        dt=report_time(a)
        iso=dt.isocalendar()
        keys={'day':dt.strftime('%Y-%m-%d'),'week':f'{iso.year}-W{iso.week:02d}',
              'month':dt.strftime('%Y-%m'),'department':a.department or 'Unassigned',
              'admin':a.actor_email or a.actor_name or 'Unknown'}
        col=ACTION_NAMES[a.action]
        for obj in (totals,*(groups[k][v] for k,v in keys.items())):
            obj[col]+=1;obj['total']+=1
    return {'totals':totals,'groups':{k:[{'label':label,**counts} for label,counts in sorted(g.items())] for k,g in groups.items()}}

@app.get('/api/reports/analytics')
@auth('super_admin','admin')
def report_analytics(user):
    month=request.args.get('month','').strip()
    if month:
        try:start,end=month_range(month)
        except ValueError as e:return jsonify(error=str(e)),400
    else:start=end=None
    department=user.department if user.role=='admin' else request.args.get('department','').strip() or None
    records=admin_audits(department,start,end)
    result=summarise(records)
    result.update(month=month or 'all',department=department or 'all',time_zone='Asia/Kolkata')
    return jsonify(result)

@app.get('/api/reports/changes.csv')
@auth('super_admin','admin')
def report_changes_csv(user):
    month=request.args.get('month','').strip()
    if month:
        try:start,end=month_range(month)
        except ValueError as e:return jsonify(error=str(e)),400
    else:start=end=None
    dept=user.department if user.role=='admin' else None
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['Time (IST)','Action','Department','Admin','Admin Email','Contact','Before','After'])
    for a in admin_audits(dept,start,end):
        before=json.loads(a.before) if a.before else {}
        after=json.loads(a.after) if a.after else {}
        writer.writerow([report_time(a).strftime('%Y-%m-%d %H:%M:%S'),a.action,a.department,a.actor_name,a.actor_email,
                         (after or before).get('name',''),readable_contact(a.before),readable_contact(a.after)])
    from flask import Response
    return Response('\ufeff'+output.getvalue(),mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="directory-changes-{month or "all"}.csv"'})

def send_monthly_report(month):
    """Run from monthly_report.py (cron/launchd), not from Flask's dev server."""
    start,end=month_range(month)
    if datetime.now(timezone.utc).replace(tzinfo=None)<end:
        raise ValueError('Monthly report can only be sent after the month ends')
    existing=db.session.get(MonthlyReportDelivery,month)
    if existing and existing.status=='sent':return 'already_sent'
    sender=os.getenv('SMTP_USER','').strip()
    password=os.getenv('SMTP_APP_PASSWORD','').replace(' ','').strip()
    recipients=sorted({u.email.strip() for u in User.query.filter_by(role='super_admin',active=True).all() if u.email})
    if not sender or not password or not recipients:raise RuntimeError('SMTP credentials or active super-admin recipients missing')
    rows=admin_audits(None,start,end)
    summary=summarise(rows)
    t=summary['totals']
    lines=[f'TSF TELEPHONE DIRECTORY — MONTHLY ADMIN CHANGE REPORT',f'Month: {month}',
           'Time zone: Asia/Kolkata (IST)','',f'Total changes: {t["total"]}',
           f'Additions: {t["additions"]}',f'Updates: {t["updates"]}',f'Deletions: {t["deletions"]}','']
    for title,key in [('Department breakdown','department'),('Admin breakdown','admin'),('Daily breakdown','day')]:
        lines.extend([title,'-'*len(title)])
        for g in summary['groups'][key]:
            lines.append(f'{g["label"]}: Added {g["additions"]} | Updated {g["updates"]} | Deleted {g["deletions"]} | Total {g["total"]}')
        if not summary['groups'][key]:lines.append('No changes')
        lines.append('')
    lines.extend(['INDIVIDUAL CHANGE LOG','---------------------'])
    for a in rows:
        lines.extend([f'Date (IST): {report_time(a).strftime("%Y-%m-%d %H:%M:%S")}',
                      f'Action: {a.action.title()}',f'Admin: {a.actor_name}',f'Admin Email: {a.actor_email}',
                      f'Department: {a.department}','Before:',readable_contact(a.before),'After:',readable_contact(a.after),''])
    if not rows:lines.append('No department-admin changes during this month.')
    msg=EmailMessage();msg['From']=sender;msg['To']=', '.join(recipients)
    msg['Subject']=f'TSF Telephone Directory | Monthly Admin Change Report | {month}'
    msg.set_content('\n'.join(lines))
    with smtplib.SMTP('smtp.gmail.com',587,timeout=30) as smtp:
        smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
        smtp.login(sender,password);smtp.send_message(msg)
    entry=existing or MonthlyReportDelivery(month=month)
    entry.status='sent';entry.sent_at=datetime.now(timezone.utc).replace(tzinfo=None)
    entry.recipients=', '.join(recipients)
    db.session.add(entry);db.session.commit()
    return 'sent'

@app.get('/api/reports/monthly-status')
@auth('super_admin')
def monthly_report_status(user):
    rows=MonthlyReportDelivery.query.order_by(MonthlyReportDelivery.month.desc()).limit(24).all()
    return jsonify([{'month':r.month,'status':r.status,'sent_at':r.sent_at.isoformat() if r.sent_at else None,'recipients':r.recipients} for r in rows])

with app.app_context():
 # Safe, additive migration for existing installations; keeps historical records.
 from sqlalchemy import inspect, text
 db.create_all()
 columns={c['name'] for c in inspect(db.engine).get_columns('audit')}
 if 'actor_role' not in columns:
  with db.engine.begin() as connection:
   connection.execute(text('ALTER TABLE audit ADD COLUMN actor_role VARCHAR(20)'))
   connection.execute(text("UPDATE audit SET actor_role = (SELECT role FROM user WHERE user.id = audit.actor_id) WHERE actor_role IS NULL"))

 if not User.query.filter_by(role='super_admin').first():
  email=os.getenv('INITIAL_ADMIN_EMAIL');password=os.getenv('INITIAL_ADMIN_PASSWORD')
  if email and password and len(password)>=10:
   db.session.add(User(name='Super Admin',email=email.lower(),password=hash_password(password),role='super_admin'));db.session.commit()
  else:print('SET INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD (10+ chars) in .env to bootstrap super admin')
if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=os.getenv('FLASK_DEBUG')=='1')
