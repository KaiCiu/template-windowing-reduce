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
    value: float  # 允许浮点数

    def to_json(self):
        data = asdict(self)
        data['ts'] = self.ts.isoformat()
        return json.dumps(data)


# 初始温度
T_env = 15.0  # 初始温度（环境温度）
T_final = 100.0  # 目标温度（沸点）
total_heating_time = 120  # 加热总时长（秒）
boiling_duration = 10  # 沸腾后维持时间（秒）

# 计算 k 值，使得 120 秒后接近 100°C
k = -math.log(0.01) / total_heating_time  # 确保 120 秒时温度达到 99% 目标值

start_time = time()  # 记录开始时间
boiling_start_time = None  # 记录沸腾开始时间
stop_time = None  # 记录停止时间

i = 0
with app.get_producer() as producer:
    while True:
        sensor_id = random.choice(["Sensor1", "Sensor2", "Sensor3", "Sensor4", "Sensor5"])

        elapsed_time = time() - start_time  # 计算当前运行时间

        if elapsed_time <= total_heating_time:
            # 指数升温公式
            current_temperature = T_env + (T_final - T_env) * (1 - math.exp(-k * elapsed_time))
        else:
            if boiling_start_time is None:
                boiling_start_time = time()  # 记录沸腾开始时间
                stop_time = boiling_start_time + boiling_duration  # 计算停止时间

            if time() >= stop_time:
                print("Simulation finished.")
                break  # 停止数据生成

            # 维持 100°C
            current_temperature = T_final

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
        sleep(random.randint(0, 1000) / 1000)  # 维持数据频率
