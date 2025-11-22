import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import urllib.request
import urllib.parse
import re
from pathlib import Path

CONFIG_FILE = Path('storyboard_config.json')

class StoryboardGenerator:
    def __init__(self):
        self.current_page = 0
        self.pages = []
        self.header = ""
        self.project_title = ""
        self.setup_gui()
        self.load_config()
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("그래픽노블 제네레이터 0.1 by 빽도")
        self.root.geometry("1000x800")
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단 컨트롤 프레임
        control_frame = ttk.LabelFrame(main_frame, text="설정 및 제어", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # API 설정 행
        api_frame = ttk.Frame(control_frame)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(side=tk.LEFT, padx=(0, 10))
        self.api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        api_key_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(api_frame, text="Model:").pack(side=tk.LEFT, padx=(10, 5))
        self.model_var = tk.StringVar(value="gemini-3-pro-preview")
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_var, width=25, 
                                   values=["gemini-3-pro-preview", "gemini-2.0-flash-exp", "gemini-2.5-pro"])
        model_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 프로젝트 제목 행
        title_frame = ttk.Frame(control_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="프로젝트 제목:").pack(side=tk.LEFT, padx=(0, 10))
        self.project_title_var = tk.StringVar()
        title_entry = ttk.Entry(title_frame, textvariable=self.project_title_var, width=50)
        title_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 버튼 행
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="설정 저장", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="설정 불러오기", command=self.load_config_dialog).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(button_frame, text="스토리보드 생성", command=self.generate_storyboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="저장", command=self.save_storyboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="불러오기", command=self.load_storyboard).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(button_frame, text="전체 이미지 생성", command=self.generate_all_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="현재 페이지 이미지 생성", command=self.generate_current_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # 입력 프레임
        input_frame = ttk.LabelFrame(main_frame, text="소설 텍스트 입력", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=5, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X)
        
        # 스토리보드 프레임
        storyboard_frame = ttk.LabelFrame(main_frame, text="스토리보드", padding=10)
        storyboard_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 좌우 분할 프레임
        split_frame = ttk.Frame(storyboard_frame)
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽 프레임 (텍스트)
        left_frame = ttk.Frame(split_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 오른쪽 프레임 (이미지)
        right_frame = ttk.LabelFrame(split_frame, text="생성된 이미지", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 헤더 프레임
        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="전체 헤드 프롬프트:").pack(anchor=tk.W)
        self.header_text = scrolledtext.ScrolledText(header_frame, height=5, wrap=tk.WORD)
        self.header_text.pack(fill=tk.X, pady=(5, 0))
        
        # 페이지 네비게이션
        nav_frame = ttk.Frame(left_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 10))
        
        ttk.Button(nav_frame, text="◀ 이전", command=self.prev_page).pack(side=tk.LEFT, padx=(0, 10))
        self.page_label = ttk.Label(nav_frame, text="Page 0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(nav_frame, text="다음 ▶", command=self.next_page).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(nav_frame, text="클립보드 복사", command=self.copy_to_clipboard).pack(side=tk.RIGHT)
        
        # 페이지 내용
        page_frame = ttk.Frame(left_frame)
        page_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(page_frame, text="페이지 내용:").pack(anchor=tk.W)
        self.page_text = scrolledtext.ScrolledText(page_frame, height=10, wrap=tk.WORD)
        self.page_text.pack(fill=tk.BOTH, expand=True)
        
        # 이미지 표시 영역
        image_canvas_frame = ttk.Frame(right_frame)
        image_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_canvas = tk.Canvas(image_canvas_frame, bg='white')
        image_scrollbar_y = ttk.Scrollbar(image_canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        image_scrollbar_x = ttk.Scrollbar(image_canvas_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=image_scrollbar_y.set, xscrollcommand=image_scrollbar_x.set)
        
        image_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        image_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.current_image = None
        self.current_photo = None
        self.current_image_path = None
        
        # 이미지 클릭 이벤트 바인딩
        self.image_canvas.bind("<Button-1>", self.on_image_click)
        
        # 상태바
        self.status_label = ttk.Label(main_frame, text="준비", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def get_project_folder(self):
        """프로젝트 폴더 경로 반환 (없으면 생성)"""
        project_title = self.project_title_var.get().strip()
        
        # 제목이 없으면 자동 생성
        if not project_title:
            projects_dir = Path('projects')
            projects_dir.mkdir(exist_ok=True)
            
            # 기존 unnamed 폴더 찾기
            existing_unnamed = [d for d in projects_dir.iterdir() 
                              if d.is_dir() and d.name.startswith('unnamed')]
            
            # 다음 번호 찾기
            max_num = 0
            for folder in existing_unnamed:
                match = re.search(r'unnamed(\d+)', folder.name)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            
            project_title = f"unnamed{max_num + 1}"
            self.project_title_var.set(project_title)
        
        # 프로젝트 폴더 생성
        project_folder = Path('projects') / project_title
        project_folder.mkdir(parents=True, exist_ok=True)
        
        return project_folder
    
    def generate_storyboard(self):
        """Gemini API를 사용해 스토리보드 생성"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("오류", "Gemini API 키를 입력해주세요.")
            return
        
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showerror("오류", "소설 텍스트를 입력해주세요.")
            return
        
        self.status_label.config(text="스토리보드 생성 중...")
        self.root.update()
        
        try:
            prompt = f"""다음 텍스트를 그래픽 노블의 스토리보드로 변환해주세요.

스토리보드 작성 규칙:
1. 전체적인 헤드 프롬프트를 먼저 작성하세요:
   - 제목
   - 그래픽 노블의 전체적인 분위기와 기조
   - 중요 등장인물들의 요약된 외모
   
2. 각 페이지는 "Page 1", "Page 2" 등으로 명확히 구분하세요.

3. 입력받은 언어로 스토리보드를 작성하되, 작중 인용이 필요한 경우 다른 언어를 사용할 수 있습니다.

4. 모든 내레이션과 대사는 제공된 텍스트 그대로 사용하세요.

5. 각 페이지마다 시각적 구성, 대사, 내레이션을 상세히 설명하세요.

입력 텍스트:
{input_text}

스토리보드를 작성해주세요:"""

            api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model_var.get()}:generateContent?key={api_key}'
            
            request_data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 8000
                }
            }
            
            req_data = json.dumps(request_data).encode('utf-8')
            request = urllib.request.Request(
                api_url,
                data=req_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(request, timeout=60) as response:
                response_data = json.loads(response.read().decode('utf-8'))
            
            if 'candidates' in response_data and response_data['candidates']:
                storyboard_text = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
                self.parse_storyboard(storyboard_text)
                self.status_label.config(text=f"스토리보드 생성 완료 - 총 {len(self.pages)}페이지")
            else:
                messagebox.showerror("오류", "스토리보드 생성에 실패했습니다.")
                self.status_label.config(text="생성 실패")
                
        except Exception as e:
            messagebox.showerror("오류", f"스토리보드 생성 중 오류 발생:\n{str(e)}")
            self.status_label.config(text="오류 발생")
    
    def parse_storyboard(self, text):
        """스토리보드 텍스트를 헤더와 페이지로 파싱"""
        # Page 1 이전까지를 헤더로 간주
        page_pattern = r'Page\s+\d+'
        first_page_match = re.search(page_pattern, text, re.IGNORECASE)
        
        if first_page_match:
            self.header = text[:first_page_match.start()].strip()
            pages_text = text[first_page_match.start():]
            
            # 페이지 분리
            page_splits = re.split(page_pattern, pages_text, flags=re.IGNORECASE)
            page_numbers = re.findall(page_pattern, pages_text, flags=re.IGNORECASE)
            
            self.pages = []
            for i, page_content in enumerate(page_splits[1:], 1):
                if i <= len(page_numbers):
                    self.pages.append({
                        'title': page_numbers[i-1],
                        'content': page_content.strip()
                    })
        else:
            # Page 구분이 없는 경우 전체를 헤더로
            self.header = text
            self.pages = []
        
        self.current_page = 0
        self.display_current_page()
    
    def display_current_page(self):
        """현재 페이지 표시"""
        # 헤더 표시
        self.header_text.delete("1.0", tk.END)
        self.header_text.insert("1.0", self.header)
        
        # 페이지 정보 업데이트
        if self.pages:
            self.page_label.config(text=f"Page {self.current_page + 1} / {len(self.pages)}")
            
            # 페이지 내용 표시 (헤더 + 페이지 통합)
            self.page_text.delete("1.0", tk.END)
            page_data = self.pages[self.current_page]
            
            # 지시문 + 헤더 + 페이지 내용 통합
            full_content = "Draw a graphic novel based on the following storyboard. You can draw graphic novels only in the language you provided, but you can use other languages ​​if you need to quote from the work.This graphic novel's page format is 1:1.4 width-to-height. Please make the panels taller.\n\n"
            full_content += f"{self.header}\n\n"
            full_content += f"{page_data['title']}\n\n{page_data['content']}"
            self.page_text.insert("1.0", full_content)
            
            # 해당 페이지의 이미지가 있으면 표시
            self.display_page_image(self.current_page + 1)
        else:
            self.page_label.config(text="Page 0 / 0")
            self.page_text.delete("1.0", tk.END)
            self.show_no_image_message()
    
    def display_page_image(self, page_num):
        """페이지 번호에 해당하는 이미지 표시"""
        try:
            project_folder = self.get_project_folder()
            images_folder = project_folder / 'images'
            image_path = images_folder / f'page_{page_num:03d}.png'
            
            if image_path.exists():
                self.display_image(image_path)
            else:
                self.show_no_image_message()
        except:
            self.show_no_image_message()
    
    def show_no_image_message(self):
        """이미지가 없을 때 메시지 표시"""
        self.current_image_path = None
        self.image_canvas.delete("all")
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            self.image_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="No image yet",
                font=('Arial', 20, 'italic'),
                fill='gray'
            )
    
    def clear_image_canvas(self):
        """이미지 캔버스 초기화"""
        self.current_image_path = None
        self.image_canvas.delete("all")
        self.current_photo = None
        self.current_image = None
    
    def on_image_click(self, event):
        """이미지 클릭 시 전체화면으로 표시"""
        if self.current_image_path:
            self.show_fullscreen_image()
    
    def show_fullscreen_image(self):
        """전체화면 이미지 뷰어"""
        if not self.current_image_path or not self.pages:
            return
        
        try:
            from PIL import Image, ImageTk
            
            # 전체화면 윈도우 생성
            fullscreen_window = tk.Toplevel(self.root)
            fullscreen_window.title("이미지 뷰어")
            fullscreen_window.attributes('-fullscreen', True)
            fullscreen_window.configure(bg='black')
            
            # 현재 페이지 번호 저장
            fs_page = {'current': self.current_page}
            
            # 메인 프레임
            main_frame = tk.Frame(fullscreen_window, bg='black')
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 이미지 라벨
            image_label = tk.Label(main_frame, bg='black')
            image_label.pack(expand=True)
            
            # 네비게이션 프레임 (하단)
            nav_frame = tk.Frame(fullscreen_window, bg='black')
            nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
            
            # 페이지 정보 라벨
            page_info_label = tk.Label(nav_frame, text="", font=('Arial', 14), 
                                       fg='white', bg='black')
            page_info_label.pack(side=tk.TOP, pady=10)
            
            # 버튼 프레임
            button_frame = tk.Frame(nav_frame, bg='black')
            button_frame.pack()
            
            # 이전 버튼
            prev_btn = tk.Button(button_frame, text="◀ 이전 (←)", 
                                font=('Arial', 12), width=15,
                                command=lambda: navigate_page(-1))
            prev_btn.pack(side=tk.LEFT, padx=20)
            
            # 다음 버튼
            next_btn = tk.Button(button_frame, text="다음 (→) ▶", 
                                font=('Arial', 12), width=15,
                                command=lambda: navigate_page(1))
            next_btn.pack(side=tk.LEFT, padx=20)
            
            # 닫기 버튼
            close_btn = tk.Button(button_frame, text="닫기 (ESC)", 
                                 font=('Arial', 12), width=15,
                                 command=lambda: close_fullscreen())
            close_btn.pack(side=tk.LEFT, padx=20)
            
            def load_image(page_num):
                """페이지 이미지 로드"""
                try:
                    project_folder = self.get_project_folder()
                    images_folder = project_folder / 'images'
                    image_path = images_folder / f'page_{page_num + 1:03d}.png'
                    
                    if image_path.exists():
                        # 이미지 로드
                        image = Image.open(image_path)
                        
                        # 스크린 크기에 맞게 조정 (네비게이션 바 공간 확보)
                        screen_width = fullscreen_window.winfo_screenwidth()
                        screen_height = fullscreen_window.winfo_screenheight() - 150
                        image.thumbnail((screen_width - 40, screen_height - 40), Image.Resampling.LANCZOS)
                        
                        # PhotoImage로 변환
                        photo = ImageTk.PhotoImage(image)
                        
                        # 이미지 표시
                        image_label.config(image=photo)
                        image_label.image = photo  # 참조 유지
                        
                        # 페이지 정보 업데이트
                        page_info_label.config(text=f"Page {page_num + 1} / {len(self.pages)}")
                    else:
                        # 이미지 없음 표시
                        image_label.config(image='', text='No image yet', 
                                         font=('Arial', 24, 'italic'), fg='gray')
                        page_info_label.config(text=f"Page {page_num + 1} / {len(self.pages)}")
                except Exception as e:
                    messagebox.showerror("오류", f"이미지 로드 실패:\n{str(e)}")
            
            def navigate_page(direction):
                """페이지 네비게이션"""
                new_page = fs_page['current'] + direction
                if 0 <= new_page < len(self.pages):
                    fs_page['current'] = new_page
                    load_image(fs_page['current'])
                    
                    # 버튼 상태 업데이트
                    prev_btn.config(state=tk.NORMAL if fs_page['current'] > 0 else tk.DISABLED)
                    next_btn.config(state=tk.NORMAL if fs_page['current'] < len(self.pages) - 1 else tk.DISABLED)
            
            def close_fullscreen(event=None):
                fullscreen_window.destroy()
            
            # 초기 이미지 로드
            load_image(fs_page['current'])
            
            # 버튼 초기 상태 설정
            prev_btn.config(state=tk.NORMAL if fs_page['current'] > 0 else tk.DISABLED)
            next_btn.config(state=tk.NORMAL if fs_page['current'] < len(self.pages) - 1 else tk.DISABLED)
            
            # 키보드 이벤트 바인딩
            fullscreen_window.bind("<Escape>", close_fullscreen)
            fullscreen_window.bind("<Left>", lambda e: navigate_page(-1))
            fullscreen_window.bind("<Right>", lambda e: navigate_page(1))
            
        except ImportError:
            messagebox.showerror("오류", "PIL(Pillow) 라이브러리가 필요합니다.\npip install Pillow")
        except Exception as e:
            messagebox.showerror("오류", f"이미지 표시 실패:\n{str(e)}")
    
    def prev_page(self):
        """이전 페이지로 이동"""
        if self.pages and self.current_page > 0:
            # 현재 페이지 내용 저장
            self.save_current_page_changes()
            self.current_page -= 1
            self.display_current_page()
    
    def next_page(self):
        """다음 페이지로 이동"""
        if self.pages and self.current_page < len(self.pages) - 1:
            # 현재 페이지 내용 저장
            self.save_current_page_changes()
            self.current_page += 1
            self.display_current_page()
    
    def save_current_page_changes(self):
        """현재 페이지의 변경사항 저장"""
        if self.pages:
            # 헤더 저장
            self.header = self.header_text.get("1.0", tk.END).strip()
            
            # 페이지 내용 저장 (지시문과 헤더 제거)
            page_content = self.page_text.get("1.0", tk.END).strip()
            
            # 지시문 제거
            if page_content.startswith("Draw a graphic novel based on the following storyboard."):
                page_content = page_content[len("Draw a graphic novel based on the following storyboard."):].strip()
            
            # 헤더 제거 (헤더가 있다면)
            if self.header and page_content.startswith(self.header):
                page_content = page_content[len(self.header):].strip()
            
            # 페이지 제목과 내용 분리
            lines = page_content.split('\n', 1)
            if len(lines) >= 2:
                self.pages[self.current_page]['title'] = lines[0].strip()
                self.pages[self.current_page]['content'] = lines[1].strip()
            else:
                self.pages[self.current_page]['content'] = page_content
    
    def copy_to_clipboard(self):
        """현재 페이지를 클립보드로 복사"""
        if not self.pages:
            messagebox.showwarning("경고", "복사할 페이지가 없습니다.")
            return
        
        # 현재 변경사항 저장
        self.save_current_page_changes()
        
        # 현재 페이지 텍스트를 그대로 복사 (이미 지시문 + 헤더 + 페이지가 통합되어 있음)
        prompt = self.page_text.get("1.0", tk.END).strip()
        
        # 클립보드에 복사
        self.root.clipboard_clear()
        self.root.clipboard_append(prompt)
        self.status_label.config(text=f"Page {self.current_page + 1} 클립보드에 복사됨")
        messagebox.showinfo("완료", "현재 페이지가 클립보드에 복사되었습니다.")
    
    def generate_image_from_prompt(self, prompt, page_num):
        """Gemini API로 이미지 생성"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("오류", "Gemini API 키를 입력해주세요.")
            return None
        
        try:
            # Gemini 3 Pro Image Preview API 사용
            api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={api_key}'
            
            request_data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            req_data = json.dumps(request_data).encode('utf-8')
            request = urllib.request.Request(
                api_url,
                data=req_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(request, timeout=180) as response:
                response_data = json.loads(response.read().decode('utf-8'))
            
            # 응답에서 이미지 데이터 추출
            if 'candidates' in response_data and response_data['candidates']:
                import base64
                parts = response_data['candidates'][0]['content']['parts']
                
                # 이미지 데이터 찾기
                image_data = None
                for part in parts:
                    if 'inlineData' in part:
                        image_data = part['inlineData']['data']
                        break
                
                if image_data:
                    # Base64 디코딩
                    image_bytes = base64.b64decode(image_data)
                    
                    # 프로젝트 폴더에 저장
                    project_folder = self.get_project_folder()
                    images_folder = project_folder / 'images'
                    images_folder.mkdir(exist_ok=True)
                    
                    image_path = images_folder / f'page_{page_num:03d}.png'
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    return image_path
                else:
                    return None
            else:
                return None
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            error_msg = f"이미지 생성 실패 (HTTP {e.code}):\n{error_body}"
            self.show_error_dialog("오류", error_msg)
            return None
        except Exception as e:
            error_msg = f"이미지 생성 실패:\n{str(e)}"
            self.show_error_dialog("오류", error_msg)
            return None
    
    def show_error_dialog(self, title, message):
        """복사 가능한 오류 메시지 창 표시"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 메시지 프레임
        msg_frame = ttk.Frame(dialog, padding=10)
        msg_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(msg_frame, text="오류 내용 (복사 가능):", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # 스크롤 가능한 텍스트 영역
        text_widget = tk.Text(msg_frame, wrap=tk.WORD, height=15)
        scrollbar = ttk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_widget.insert("1.0", message)
        text_widget.config(state=tk.NORMAL)  # 복사 가능하도록 설정
        
        # 버튼 프레임
        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill=tk.X)
        
        def copy_all():
            dialog.clipboard_clear()
            dialog.clipboard_append(message)
            messagebox.showinfo("완료", "오류 메시지가 클립보드에 복사되었습니다.", parent=dialog)
        
        ttk.Button(btn_frame, text="전체 복사", command=copy_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="닫기", command=dialog.destroy).pack(side=tk.LEFT)
    
    def display_image(self, image_path):
        """캔버스에 이미지 표시"""
        try:
            from PIL import Image, ImageTk
            
            # 이미지 경로 저장
            self.current_image_path = image_path
            
            # 이미지 열기
            image = Image.open(image_path)
            
            # 캔버스 크기에 맞게 조정
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                image.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
            
            # PhotoImage로 변환
            self.current_photo = ImageTk.PhotoImage(image)
            
            # 캔버스 초기화 후 이미지 표시
            self.image_canvas.delete("all")
            self.current_image = self.image_canvas.create_image(
                canvas_width // 2, 
                canvas_height // 2, 
                image=self.current_photo, 
                anchor=tk.CENTER
            )
            
        except ImportError:
            messagebox.showerror("오류", "PIL(Pillow) 라이브러리가 필요합니다.\npip install Pillow")
        except Exception as e:
            messagebox.showerror("오류", f"이미지 표시 실패:\n{str(e)}")
    
    def generate_current_image(self):
        """현재 페이지 이미지 생성"""
        if not self.pages:
            messagebox.showwarning("경고", "생성할 페이지가 없습니다.")
            return
        
        # 현재 변경사항 저장
        self.save_current_page_changes()
        
        self.status_label.config(text=f"Page {self.current_page + 1} 이미지 생성 중...")
        self.root.update()
        
        # 현재 페이지 프롬프트 생성
        prompt = self.page_text.get("1.0", tk.END).strip()
        
        # 이미지 생성
        image_path = self.generate_image_from_prompt(prompt, self.current_page + 1)
        
        if image_path:
            self.display_image(image_path)
            self.status_label.config(text=f"Page {self.current_page + 1} 이미지 생성 완료")
            messagebox.showinfo("완료", f"이미지가 생성되었습니다.\n{image_path}")
        else:
            self.status_label.config(text=f"Page {self.current_page + 1} 이미지 생성 실패")
    
    def generate_all_images(self):
        """모든 페이지 이미지 일괄 생성"""
        if not self.pages:
            messagebox.showwarning("경고", "생성할 페이지가 없습니다.")
            return
        
        # 현재 변경사항 저장
        self.save_current_page_changes()
        
        result = messagebox.askyesno(
            "확인", 
            f"총 {len(self.pages)}개의 페이지 이미지를 생성합니다.\n시간이 오래 걸릴 수 있습니다. 계속하시겠습니까?"
        )
        
        if not result:
            return
        
        success_count = 0
        fail_count = 0
        
        for i, page_data in enumerate(self.pages):
            self.status_label.config(text=f"Page {i + 1}/{len(self.pages)} 이미지 생성 중...")
            self.root.update()
            
            # 프롬프트 생성
            prompt = f"Draw a graphic novel based on the following storyboard.\n\n"
            prompt += f"{self.header}\n\n"
            prompt += f"{page_data['title']}\n\n{page_data['content']}"
            
            # 이미지 생성
            image_path = self.generate_image_from_prompt(prompt, i + 1)
            
            if image_path:
                success_count += 1
                # 마지막 이미지를 화면에 표시
                if i == len(self.pages) - 1:
                    self.display_image(image_path)
            else:
                fail_count += 1
        
        self.status_label.config(text=f"이미지 생성 완료: 성공 {success_count}개, 실패 {fail_count}개")
        messagebox.showinfo(
            "완료", 
            f"이미지 생성이 완료되었습니다.\n성공: {success_count}개\n실패: {fail_count}개"
        )
    
    def save_storyboard(self):
        """스토리보드를 파일로 저장"""
        if not self.header and not self.pages:
            messagebox.showwarning("경고", "저장할 스토리보드가 없습니다.")
            return
        
        # 현재 변경사항 저장
        self.save_current_page_changes()
        
        # 프로젝트 폴더 가져오기
        project_folder = self.get_project_folder()
        
        # 기본 파일명을 프로젝트 폴더 내에 설정
        default_filename = project_folder / "storyboard.json"
        
        file_path = filedialog.asksaveasfilename(
            title="스토리보드 저장",
            initialdir=project_folder,
            initialfile="storyboard.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                data = {
                    'header': self.header,
                    'pages': self.pages,
                    'project_title': self.project_title_var.get()
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.status_label.config(text=f"저장 완료: {file_path}")
                messagebox.showinfo("완료", "스토리보드가 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패:\n{str(e)}")
    
    def load_storyboard(self):
        """스토리보드를 파일에서 불러오기"""
        file_path = filedialog.askopenfilename(
            title="스토리보드 불러오기",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.header = data.get('header', '')
                self.pages = data.get('pages', [])
                self.project_title_var.set(data.get('project_title', ''))
                self.current_page = 0
                self.display_current_page()
                self.status_label.config(text=f"불러오기 완료: {file_path}")
                messagebox.showinfo("완료", "스토리보드를 불러왔습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"불러오기 실패:\n{str(e)}")
    
    def save_config(self):
        """설정 저장"""
        try:
            config = {
                'api_key': self.api_key_var.get(),
                'model': self.model_var.get()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("완료", "설정이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패:\n{str(e)}")
    
    def load_config_dialog(self):
        """설정 불러오기 대화상자"""
        file_path = filedialog.askopenfilename(
            title="설정 불러오기",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_config_from_file(file_path)
    
    def load_config(self):
        """기본 설정 파일 로드"""
        if CONFIG_FILE.exists():
            self.load_config_from_file(CONFIG_FILE)
    
    def load_config_from_file(self, file_path):
        """파일에서 설정 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.api_key_var.set(config.get('api_key', ''))
            self.model_var.set(config.get('model', 'gemini-2.0-flash-exp'))
        except Exception as e:
            pass
    
    def run(self):
        """GUI 실행"""
        def on_closing():
            # 종료 시 현재 변경사항 저장 확인
            if self.pages:
                result = messagebox.askyesnocancel(
                    "종료", 
                    "변경사항을 저장하시겠습니까?"
                )
                if result is None:  # Cancel
                    return
                elif result:  # Yes
                    self.save_current_page_changes()
                    self.save_storyboard()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = StoryboardGenerator()
    app.run()