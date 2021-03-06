# api.py
import json
from flask import Flask, render_template, request, send_file
import jobs
import sys
import os.path as path
from os import listdir
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "."

@app.route('/')
def main():
  return render_template("page.html")


@app.route('/login', methods=['GET'])
def login():
  bid = request.args.get('id', default='', type=str)
  if jobs.bid_exists(bid):
    print("ACCESSING ACCT: " + str(bid), file=sys.stderr)
    return json.dumps(jobs.rd2.hgetall(bid))
  else:
    return 'ACCOUNT NUMBER NOT FOUND'


@app.route('/create', methods=['GET'])
def create():
  bid = jobs.create_account()
  return jobs.rd2.hgetall(bid)


@app.route('/delete', methods=['GET'])
def delete():
  bid = request.args.get('id', default='', type=str)
  if jobs.bid_exists(bid):
    jobs.rd2.delete(bid)
    return 'completed'
  else:
    return 'ACCOUNT NUMBER NOT FOUND'


@app.route('/accountids', methods=['GET'])
def account_ids():
  return json.dumps(jobs.rd2.keys())


@app.route('/jobids', methods=['GET'])
def job_ids():
  return json.dumps(jobs.rd1.keys())


@app.route('/jobs', methods=['GET'])
def get_jobs():
  job_list = []
  for key in jobs.rd4.keys():
    job_list.append(jobs.rd4.hgetall(key))
  jobs.rd4.flushdb()
  return json.dumps(job_list)


@app.route('/graph/spending', methods=['GET'])
def request_spending_graph():
  print("Directories:" + str(listdir()))
  bid = request.args.get('id', default='', type=str)
  print("Account ID: {}".format(bid), file=sys.stderr)
  # Extra random data for clearing the cache
  rand = request.args.get('rand', default='', type=str)
  img = jobs.get_spending_graph(bid)[0]
  path = str(uuid.uuid4()) + ".png"
  with open(path, 'wb') as f:
    f.write(img)
  return send_file(path, mimetype='image/png', as_attachment=True)


@app.route('/graph/histogram', methods=['GET'])
def request_hourly_histogram():
  bid = request.args.get('id', default='', type=str)
  print("Account ID: {}".format(bid), file=sys.stderr)
  # Extra random data for clearing the cache
  rand = request.args.get('rand', default='', type=str)
  img = jobs.get_hrly_histogram(bid)[0]
  path = str(uuid.uuid4()) + ".png"
  with open(path, 'wb') as f:
    f.write(img)
  return send_file(path, mimetype='image/png', as_attachment=True)


@app.route('/generate_accounts', methods=['GET'])
def gen_accts():
  print("Generating accounts...", file=sys.stderr)
  jobs.q1.put("generate random accounts")
  return "Confirmed"


@app.route('/nuke', methods=['GET'])
def clear_db():
  print("Nuking...", file=sys.stderr)
  jobs.rd1.flushdb()
  jobs.rd2.flushdb()
  jobs.rd3.flushdb()
  jobs.rd4.flushdb()
  jobs.q1.clear()
  jobs.q2.clear()
  return "Nuked"


@app.route('/transaction/deposit', methods=['GET'])
def deposit():
  bid = request.args.get('id', default='', type=str)
  amount = request.args.get('amount', default=0, type=float)
  if jobs.bid_exists(bid):
    jobs.create_job(bid, amount)
    print("Depositing ${} into acct {}".format(amount, bid), file=sys.stderr)
    return jobs.rd2.hget(bid, 'balance')
  else:
    print("Invalid acct# to deposit ${} to acct {}".format(amount, bid), file=sys.stderr)
    return 'ACCOUNT NUMBER NOT FOUND'

@app.route('/transaction/withdraw', methods=['GET'])
def withdraw():
  bid = request.args.get('id', default='', type=str)
  amount = (request.args.get('amount', default=0, type=float))
  amount *= -1 # needs to be negative
  if jobs.bid_exists(bid):
    if jobs.can_withdraw(bid, amount):
      jobs.create_job(bid, amount)
      print("Withdrawing ${} from acct {}".format(amount, bid), file=sys.stderr)
      return jobs.rd2.hget(bid, 'balance')
    else:
      print("Invalid funds to withdraw ${} from acct {}".format(amount, bid), file=sys.stderr)
      return 'NOT ENOUGH BALANCE'
  else:
    print("Invalid acct# to withdraw ${} from acct {}".format(amount, bid), file=sys.stderr)
    return 'ACCOUNT NUMBER NOT FOUND'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
