from jobs import q2, generate_spending_graph


@q2.worker
def execute_job(jid):
    print("Processing graphing job {}".format(jid))
    generate_spending_graph(jid)

execute_job()
