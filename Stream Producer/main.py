from dataclasses import dataclass, asdict  # used to define the data schema
from datetime import datetime  # used to manage timestamps
from time import sleep  # used to slow down the data generator
import uuid  # used for message id creation
import json  # used for serializing data
import random

from quixstreams import Application

app = Application.Quix()
destination_topic = app.topic(name='raw-temp-data', value_serializer="json")


@dataclass
class Temperature:
    ts: datetime
    value: float  # Change to float for higher precision

    def to_json(self):
        # Convert the dataclass to a dictionary
        data = asdict(self)
        # Format the datetime object as a string
        data['ts'] = self.ts.isoformat()
        # Serialize the dictionary to a JSON string
        return json.dumps(data)


i = 0
mean_temperature = 22.0  # Mean temperature in Celsius (e.g., room temperature)
std_dev_temperature = 5.0  # Standard deviation, higher value means more fluctuation

with app.get_producer() as producer:
    while i < 10000:
        sensor_id = random.choice(["Sensor1", "Sensor2", "Sensor3", "Sensor4", "Sensor5"])
        # Simulate temperature with normal distribution
        temperature_value = random.gauss(mean_temperature, std_dev_temperature)
        temperature_value = round(temperature_value, 2)  # Round to 2 decimal places to make it realistic
        temperature = Temperature(datetime.now(), temperature_value)
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
        sleep(random.randint(0, 1000) / 1000)
