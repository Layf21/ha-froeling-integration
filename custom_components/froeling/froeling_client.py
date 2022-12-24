import requests

headers = {
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "Froeling PROD/2107.1 (com.froeling.connect-ios; build:2107.1.01; iOS 14.8.0) Alamofire/4.8.1",
    "Accept-Language": "de",
}


class Facility:
    def __init__(self, session, token, facility_id, name, friendly_name):
        self.session = session
        self.token = token
        self.id = facility_id
        self.name = name
        self.friendly_name = friendly_name
        self.devices = {}
        self.info = {}

    def __repr__(self):
        return f"<Device {self.id}: {self.friendly_name}>"

    def update_general_data(self):
        res = requests.get(
            f"https://connect-api.froeling.com/fcs/v1.0/resources/user/{self.session['userId']}/facility/{self.id}/overview",
            headers=headers | {"Authorization": self.token},
            timeout=10,
        )
        self.info = res.json()
        self.devices = {
            component["componentId"]: component["displayName"]
            for component in self.info["components"]
        }


class Froeling:
    facilities: list[Facility]

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.session = None
        self.token = None
        self.facilities = []

    def login(self):
        res = requests.post(
            "https://connect-api.froeling.com/app/v1.0/resources/loginNew",
            headers=headers | {"Content-Type": "application/json"},
            json={
                "osType": "IOS",
                "userName": self.username,
                "password": self.password,
            },
            timeout=20,
        )
        if res.status_code == 403:
            raise AuthenticationError(res.text)
        self.session = res.json()
        self.token = res.headers["authorization"]
        return True

    def getFacilities(self):
        url = "https://connect-api.froeling.com/app/v1.0/resources/user/getFacilities"  # "https://connect-api.froeling.com/app/v1.0/resources/user/getServiceFacilities"
        res = requests.get(
            url, timeout=10, headers=headers | {"Authorization": self.token}
        )
        if res.status_code == 403:
            raise AuthenticationError(res.text)
        data = res.json()
        for d in data:
            facility = Facility(
                self.session, self.token, d["id"], d["name"], d["description"]
            )
            self.facilities.append(facility)


class AuthenticationError(Exception):
    pass
