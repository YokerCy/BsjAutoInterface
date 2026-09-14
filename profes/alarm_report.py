class AlarmReport:
    def __init__(self, client):
        self.client = client

    # 获取报警类型
    def get_alarm_type(self):
        res = self.client.send_by_key(
            "GET",
            "get_alarm_type",
            json={"type": "0"}
        )
        return res.json()

        # 获取报警数据
    def get_alarm_message(self, device_id):
        res = self.client.send_api(
            "POST",
            "alarm_info",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": "2026-06-03 00:00:00",
                "endTime": "2026-06-03 23:59:59"
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

        # 获取ai报警数据
    def get_ai_event_alarm_message(self, device_id):
        res = self.client.send_api(
            "POST",
            "ai_event_alarm_info",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": "2026-06-03 00:00:00",
                "endTime": "2026-06-03 23:59:59"
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

    def get_parking_report_list(self, device_id):
        res = self.client.send_api(
            "POST",
            "parking_record",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": "2026-06-03 00:00:00",
                "endTime": "2026-06-03 23:59:59"
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

