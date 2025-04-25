import pika
import json
import pandas as pd
from sqlalchemy import create_engine

credentials = pika.PlainCredentials('admin', 'admin')
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', 5672, '/', credentials))
channel = connection.channel()
channel.queue_declare(queue='sales_data_queue', durable=True)

def callback(ch, method, properties, body):
    data = json.loads(body)
    df = pd.DataFrame(data)
    engine = create_engine('postgresql://postgres:password@postgres:5432/retail_db')
    df.to_sql('sales', engine, if_exists='append', index=False)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='sales_data_queue', on_message_callback=callback)
channel.start_consuming()