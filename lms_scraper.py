import os
import requests

class LMSScraper:
    def __init__(self, base_url="https://isikuniversity.mrooms.net"):
        self.base_url = base_url.rstrip("/")
        self.rest_endpoint = f"{self.base_url}/webservice/rest/server.php"
        self.token_endpoint = f"{self.base_url}/login/token.php"
        self.service = "moodle_mobile_app"
        self.session = requests.Session()
        
        # Keep track of tokens per user to avoid fetching repeatedly in a session
        self.tokens = {}
        self.user_ids = {}

    def _get_token(self, username, password):
        if username in self.tokens:
            return self.tokens[username]

        params = {
            "username": username,
            "password": password,
            "service": self.service
        }
        
        try:
            response = self.session.post(self.token_endpoint, data=params, timeout=10)
            data = response.json()
            
            if "token" in data:
                self.tokens[username] = data["token"]
                return data["token"]
            else:
                return None
        except Exception as e:
            print(f"Token Error: {e}")
            return None

    def _get_user_id(self, token, username):
        if username in self.user_ids:
            return self.user_ids[username]

        params = {
            "wstoken": token,
            "wsfunction": "core_webservice_get_site_info",
            "moodlewsrestformat": "json"
        }
        
        try:
            response = self.session.post(self.rest_endpoint, data=params, timeout=10)
            data = response.json()
            if "userid" in data:
                self.user_ids[username] = data["userid"]
                return data["userid"]
        except Exception as e:
            print(f"User ID Error: {e}")
        return None

    def login_test(self, username, password):
        """Test login by attempting to retrieve a token."""
        token = self._get_token(username, password)
        return token is not None

    def get_courses(self, username, password):
        """Get user courses via Moodle API."""
        token = self._get_token(username, password)
        if not token:
            return []

        user_id = self._get_user_id(token, username)
        if not user_id:
            return []

        params = {
            "wstoken": token,
            "wsfunction": "core_enrol_get_users_courses",
            "userid": user_id,
            "moodlewsrestformat": "json"
        }

        try:
            response = self.session.post(self.rest_endpoint, data=params, timeout=10)
            data = response.json()
            
            courses = []
            if isinstance(data, list):
                for course in data:
                    # Provide a link that works in the browser as fallback context
                    courses.append({
                        "id": course.get("id"),
                        "name": course.get("fullname") or course.get("shortname"),
                        "link": f"{self.base_url}/course/view.php?id={course.get('id')}"
                    })
            return courses
        except Exception as e:
            print(f"Course Fetch Error: {e}")
            return []

    def get_materials(self, username, password, course_link_or_id):
        """Get materials for a specific course via Moodle API."""
        token = self._get_token(username, password)
        if not token:
            return []

        # Determine course ID
        course_id = None
        if isinstance(course_link_or_id, int):
            course_id = course_link_or_id
        elif isinstance(course_link_or_id, str):
            if "?id=" in course_link_or_id:
                try:
                    course_id = int(course_link_or_id.split("?id=")[1].split("&")[0])
                except:
                    pass

        if not course_id:
            return []

        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_contents",
            "courseid": course_id,
            "moodlewsrestformat": "json"
        }

        materials = []
        try:
            response = self.session.post(self.rest_endpoint, data=params, timeout=15)
            sections = response.json()
            
            if isinstance(sections, list):
                for section in sections:
                    for module in section.get("modules", []):
                        modname = module.get("modname")
                        
                        # Handle resources (files) and folders
                        if modname in ["resource", "folder"]:
                            for content in module.get("contents", []):
                                if content.get("type") == "file":
                                    file_url = content.get("fileurl")
                                    # Moodle token URLs require appending the token to bypass login
                                    if file_url:
                                        materials.append({
                                            "title": content.get("filename", module.get("name")),
                                            "link": f"{file_url}&token={token}" if "?" in file_url else f"{file_url}?token={token}"
                                        })
            return materials
        except Exception as e:
            print(f"Material Fetch Error: {e}")
            return []

    def download_materials(self, username, password, material_links, download_dir="temp_downloads"):
        """Download materials directly using requests session."""
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        downloaded_files = []
        
        for material_link in material_links:
            try:
                # Extract original filename from URL or header if possible, else generic
                filename = "downloaded_file"
                if "filename=" in material_link:
                    filename = material_link.split("filename=")[1].split("&")[0]
                elif material_link.split("/")[-1].split("?")[0]:
                    filename = material_link.split("/")[-1].split("?")[0]
                
                # Sanitize filename
                import urllib.parse
                filename = urllib.parse.unquote(filename)
                
                file_path = os.path.join(download_dir, filename)
                
                # Direct HTTP download
                response = self.session.get(material_link, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(file_path)
            except Exception as e:
                print(f"Download Error for {material_link}: {e}")

        return downloaded_files
