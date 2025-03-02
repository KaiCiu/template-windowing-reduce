from dataclasses import dataclass, asdict
from datetime import datetime
from time import sleep, time
import uuid
import json
import random
import math
import os

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
        return data  # 返回字典，而不是 JSON 字符串（方便后续存文件）


# 参数设置
T_ambient = 15.0  # 初始温度
T_final = 100.0  # 目标温度
total_heating_time = 120  # 加热时间
boiling_duration = 10  # 沸腾维持时间

# 计算 k 值
k = -math.log(0.01) / total_heating_time  # 让 120 秒后温度接近 100°C

start_time = time()
boiling_start_time = None
stop_time = None

data_records = []  # 用于存储所有温度数据

i = 0
with app.get_producer() as producer:
    while True:
        sensor_id = random.choice(["Sensor1", "Sensor2", "Sensor3", "Sensor4", "Sensor5"])
        elapsed_time = time() - start_time  # 计算运行时间

        if elapsed_time <= total_heating_time:
            # 指数升温公式
            current_temperature = T_ambient + (T_final - T_ambient) * (1 - math.exp(-k * elapsed_time))
        else:
            if boiling_start_time is None:
                boiling_start_time = time()
                stop_time = boiling_start_time + boiling_duration  # 计算停止时间

            if time() >= stop_time:
                print("Simulation finished.")
                break  # 停止数据生成

            # 维持 100°C
            current_temperature = T_final

        # 生成数据
        temperature = Temperature(datetime.now(), round(current_temperature, 2))
        data_dict = temperature.to_json()  # 转成字典
        data_records.append(data_dict)  # 存入列表

        # 发送到 Quix
        serialized = destination_topic.serialize(
            key=sensor_id, value=json.dumps(data_dict), headers={"uuid": str(uuid.uuid4())}
        )
        producer.produce(
            topic=destination_topic.name,
            headers=serialized.headers,
            key=serialized.key,
            value=serialized.value,
        )

        i += 1
        sleep(random.randint(0, 1000) / 1000)  # 维持数据频率

# 生成文件名（包含处理完成时间）
finish_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_name = f"temperature_data_{finish_time}.json"
file_path = os.path.join(os.getcwd(), file_name)

# 保存数据到 JSON 文件
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data_records, f, indent=4)

