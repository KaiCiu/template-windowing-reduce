from dataclasses import dataclass, asdict
from datetime import datetime
from time import sleep, time
import uuid
import json
import random

from quixstreams import Application

app = Application.Quix()
destination_topic = app.topic(name='raw-temp-data', value_serializer="json")


@dataclass
class Temperature:
    ts: datetime
    value: float  # 允许浮点数

    def to_json(self):
        data = asdict(self)
        data['ts'] = self.ts.isoformat()
        return json.dumps(data)


# 初始温度
current_temperature = 20.0  # 常温
boiling_temperature = 100.0  # 水的沸点
heating_time = 60  # 假设60秒加热到沸点
boiling_duration = 10  # 沸腾后维持10秒

# 计算每秒温升
temperature_increment = (boiling_temperature - current_temperature) / heating_time

start_time = time()  # 记录加热开始时间
boiling_start_time = None  # 记录沸腾开始时间
stop_time = None  # 记录停止时间

i = 0
with app.get_producer() as producer:
    while True:
        sensor_id = random.choice(["Sensor1", "Sensor2", "Sensor3", "Sensor4", "Sensor5"])

        elapsed_time = time() - start_time  # 计算运行了多久

        if current_temperature < boiling_temperature:
            # 线性升温
            current_temperature += temperature_increment
        else:
            if boiling_start_time is None:
                boiling_start_time = time()  # 记录沸腾的开始时间
                stop_time = boiling_start_time + boiling_duration  # 计算停止时间

            if time() >= stop_time:
                print("Simulation finished.")
                break  # 停止数据生成

        # 确保温度不会超过沸点
        current_temperature = min(current_temperature, boiling_temperature)

        # 生成温度数据
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
        sleep(random.randint(0, 1000) / 1000)  # 维持原来的数据频率
