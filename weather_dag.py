from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
import json
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
import pandas as pd




def kelvin_to_fahrenheit(temp_in_kelvin):
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return temp_in_fahrenheit


def transform_load_data(task_instance):
    data = task_instance.xcom_pull(task_ids="extract_weather_data")
    city = data["name"]
    weather_description = data["weather"][0]['description']
    temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp"])
    feels_like_farenheit= kelvin_to_fahrenheit(data["main"]["feels_like"])
    min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
    max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

    transformed_data = {"City": city,
                        "Description": weather_description,
                        "Temperature (F)": temp_farenheit,
                        "Feels Like (F)": feels_like_farenheit,
                        "Minimun Temp (F)":min_temp_farenheit,
                        "Maximum Temp (F)": max_temp_farenheit,
                        "Pressure": pressure,
                        "Humidty": humidity,
                        "Wind Speed": wind_speed,
                        "Time of Record": time_of_record,
                        "Sunrise (Local Time)":sunrise_time,
                        "Sunset (Local Time)": sunset_time                        
                        }
    transformed_data_list = [transformed_data]
    df_data = pd.DataFrame(transformed_data_list)
    aws_credentials = {"key":"ASIASOWDKPMHHMSCAUEW","secret": "Fu2/t3pujpwQ9C45vfPt6B4ggRahXKFiN5bEz/p0","token": "IQoJb3JpZ2luX2VjEHsaCXVzLWVhc3QtMSJHMEUCIHOYVkLikBXOo55zIl/YpMSrfg02AmHr4bW+igvfZGcXAiEAn9ls7/4KG8C6GDMWr1XpAmmlnNaO8NVJEaOewtvo2QAq9AEI8///////////ARABGgwxNjg5ODcwOTc4NzAiDNdk8oOj8Du2mEAeUSrIAbxoJuiXHaa2+IHrziWaZ9AaMT274zVDpVqWCbD3un3Hrs//0+9uOb8sd2NuC2qAT6ZkhEkZfJrR94o25LDEgJ+q9iqXCIU9nPisaBj4qflpchf/x9lADQoOZkCl0ykxreN0AQSK74xSYGxragJk/0baeh7B6CR+FAQoqpVmX2tMwZLYA+bfo0nJp5WPIFNr4NWmeETel2ow6nMKcJq3hvQjn/rbw+MU1jFyYqFB3MMaZrBRzFfq+piHpt7gP7MqahlqXfjKLIMkMJG62LIGOpgB5d9ADATvbrpSV58U31T+87DRK0e3gC5oq0/VNcF3zxZ1C2qKL1Ho5DiwSgqU4U4OomEwrA7z2ScDlhM4T4nQ0wjhNY/1fNcpBBBg0T4PLsp6ZY+iKHiz/LfWTDRkClAg/jXx2VOzAdyt1Heb9sZEPaE8dZqZfO4NqW59PlQU6AQAofe4Zr2Woav/3fUF9JIBsV41oRpPDQc="}

    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = 'current_weather_data_portland_' + dt_string
    df_data.to_csv(f"s3://weatherapiairflowyoutubebucket-yml/{dt_string}.csv", index=False, storage_options=aws_credentials)



default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 8),
    'email': ['myemail@domain.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}



with DAG('weather_dag',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:


        is_weather_api_ready = HttpSensor(
        task_id ='is_weather_api_ready',
        http_conn_id='weathermap_api',
        endpoint='/data/2.5/weather?q=Portland&APPID=5031cde3d1a8b9469fd47e998d7aef79'
        )


        extract_weather_data = SimpleHttpOperator(
        task_id = 'extract_weather_data',
        http_conn_id = 'weathermap_api',
        endpoint='/data/2.5/weather?q=Portland&APPID=5031cde3d1a8b9469fd47e998d7aef79',
        method = 'GET',
        response_filter= lambda r: json.loads(r.text),
        log_response=True
        )

        transform_load_weather_data = PythonOperator(
        task_id= 'transform_load_weather_data',
        python_callable=transform_load_data
        )




        is_weather_api_ready >> extract_weather_data >> transform_load_weather_data
