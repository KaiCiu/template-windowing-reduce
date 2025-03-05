from dataclasses import dataclass, asdict
from datetime import datetime
from time import sleep, time
import uuid
import json
import random
import math

from quixstreams import Application

app = Application.Quix()
destination_topic = app.topic(name='raw-temp-data', value_serializer="json")

@dataclass
class Temperature:
    ts: datetime
    value: float  

    def to_json(self):
        data = asdict(self)
        data['ts'] = self.ts.isoformat()
        return json.dumps(data)


T_ambient = 15.0  
T_final = 100.0  
total_heating_time = 120  
boiling_duration = 10  


k = -math.log(0.01) / total_heating_time  

start_time = time()  
boiling_start_time = None  
stop_time = None  

i = 0
with app.get_producer() as producer:
    while True:
        sensor_id = random.choice(["Sensor1", "Sensor2", "Sensor3", "Sensor4", "Sensor5"])
        
        elapsed_time = time() - start_time 
        
        if elapsed_time <= total_heating_time:
            
            current_temperature = T_ambient + (T_final - T_ambient) * (1 - math.exp(-k * elapsed_time))
        else:
            if boiling_start_time is None:
                boiling_start_time = time()  
                stop_time = boiling_start_time + boiling_duration  
            
            if time() >= stop_time:
                print("Simulation finished.")
                break  
           
            current_temperature = T_final
        
        
        temperature = Temperature(datetime.now(), round(current_temperature, 2))
        value = temperature.to_json()

        print(f"Producing value {value}")
        serialized = destination_topic.serialize(
            key=sensor_id, value=value, headers={"uuid": str(uuid.uuid4())}
        )
        producer.produce(
            topic=destination_topic.name,
            headers=serialized.headers,
            key=serialized.key,
            value=serialized.value,
        )

        i += 1
        sleep(random.randint(0, 1000) / 2000)  
