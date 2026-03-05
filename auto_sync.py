import json
import time
import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Nama folder tempat nyimpen hasil generate
OUTPUT_DIR = "output"

def update_files(data):
    # Bikin folder otomatis kalau belum ada
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Simpan JSON ke dalam folder output
    json_path = os.path.join(OUTPUT_DIR, 'tugas.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    total_tugas = len(data) if data else 0
    tugas_selesai = sum(1 for t in data if "✅" in t['status']) if data else 0
    tugas_belum = total_tugas - tugas_selesai

    json_data_str = json.dumps(data)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ETHOL Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #09090b; color: #f4f4f5; overflow-x: hidden; }}
            .glass-card {{ background-color: #18181b; border: 1px solid #27272a; transition: all 0.2s ease; cursor: pointer; }}
            .glass-card:hover {{ border-color: #3f3f46; transform: translateY(-3px); box-shadow: 0 12px 30px -10px rgba(0,0,0,0.6); }}
            .custom-scrollbar::-webkit-scrollbar {{ width: 6px; }}
            .custom-scrollbar::-webkit-scrollbar-track {{ background: transparent; }}
            .custom-scrollbar::-webkit-scrollbar-thumb {{ background: #27272a; border-radius: 10px; }}
            .custom-scrollbar::-webkit-scrollbar-thumb:hover {{ background: #3f3f46; }}
            
            /* Animasi Modal */
            .modal-overlay {{ opacity: 0; pointer-events: none; transition: opacity 0.3s ease; }}
            .modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
            .modal-content {{ transform: translateY(20px) scale(0.95); opacity: 0; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }}
            .modal-overlay.active .modal-content {{ transform: translateY(0) scale(1); opacity: 1; }}
        </style>
    </head>
    <body class="p-6 md:p-10 antialiased custom-scrollbar selection:bg-cyan-500/30">
        <div class="max-w-7xl mx-auto">
            
            <header class="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-zinc-800 pb-8">
                <div>
                    <div class="flex flex-wrap items-center gap-3 mb-3">
                        <span class="px-3 py-1 rounded-md bg-zinc-800/80 text-zinc-400 text-[10px] font-bold uppercase tracking-widest border border-zinc-700/50">PENS • 2 D4 IT B</span>
                        <span class="px-3 py-1 rounded-md bg-cyan-500/10 text-cyan-400 text-[10px] font-bold uppercase tracking-widest border border-cyan-500/20">Ahmad Syahani</span>
                    </div>
                    <h1 class="text-3xl md:text-4xl font-bold tracking-tight text-zinc-100">ETHOL Tasks.</h1>
                </div>
                
                <div class="flex gap-3">
                    <div class="glass-card rounded-xl px-5 py-3 text-center min-w-[90px]">
                        <p class="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Total</p>
                        <p class="text-2xl font-semibold text-zinc-100">{total_tugas}</p>
                    </div>
                    <div class="glass-card rounded-xl px-5 py-3 text-center min-w-[90px]">
                        <p class="text-[9px] font-bold text-rose-500 uppercase tracking-widest mb-1">Belum</p>
                        <p class="text-2xl font-semibold text-rose-400">{tugas_belum}</p>
                    </div>
                    <div class="glass-card rounded-xl px-5 py-3 text-center min-w-[90px]">
                        <p class="text-[9px] font-bold text-emerald-500 uppercase tracking-widest mb-1">Selesai</p>
                        <p class="text-2xl font-semibold text-emerald-400">{tugas_selesai}</p>
                    </div>
                </div>
            </header>

            <div id="tasks" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    """
    
    if not data:
        html_content += '''
                <div class="col-span-full py-20 flex flex-col items-center justify-center text-center border border-dashed border-zinc-800 rounded-2xl bg-zinc-900/30">
                    <span class="text-5xl mb-4">🍻</span>
                    <h3 class="text-xl font-semibold text-zinc-300 mb-1">Tidak ada tugas aktif</h3>
                    <p class="text-zinc-500 text-sm max-w-sm">Jadwal bersih! Selamat bersantai atau lanjut ngerjain project.</p>
                </div>
        '''
    else:
        for idx, t in enumerate(data):
            is_done = "Selesai" in t['status']
            badge_class = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" if is_done else "bg-rose-500/10 text-rose-400 border border-rose-500/20"
            status_text = t['status'].replace("✅ ", "").replace("⚠️ ", "")
            
            has_file = 'file' in t and len(t['file']) > 0
            file_icon = '''<svg class="w-3.5 h-3.5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>''' if has_file else ''

            html_content += f'''
                <div class="glass-card rounded-2xl p-6 flex flex-col h-full group" onclick="openModal({idx})">
                    <div class="flex justify-between items-start mb-4 gap-4">
                        <span class="text-[11px] font-semibold text-zinc-500 tracking-wider uppercase line-clamp-1">{t['matkul']}</span>
                        <div class="flex gap-2 items-center">
                            {file_icon}
                            <span class="shrink-0 px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-widest {badge_class}">
                                {status_text}
                            </span>
                        </div>
                    </div>
                    
                    <h2 class="text-lg font-semibold text-zinc-100 mb-2 leading-snug">{t['judul']}</h2>
                    <p class="text-sm text-zinc-400 mb-6 line-clamp-2 flex-grow leading-relaxed">{t['description']}</p>
                    
                    <div class="mt-auto pt-5 border-t border-zinc-800/60 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-zinc-800/80 text-zinc-400">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                            </div>
                            <div>
                                <p class="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mb-0.5">Tenggat Waktu</p>
                                <p class="text-[13px] font-medium text-zinc-300">{t['deadline']}</p>
                            </div>
                        </div>
                        <span class="text-[10px] font-medium text-zinc-500 group-hover:text-cyan-400 transition-colors">Detail ↗</span>
                    </div>
                </div>
            '''
            
    html_content += f"""
            </div>
        </div>

        <div id="taskModal" class="modal-overlay fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
            <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" onclick="closeModal()"></div>
            
            <div class="modal-content relative bg-[#0f0f13] border border-zinc-800 shadow-2xl rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
                <div class="flex justify-between items-center p-5 md:p-6 border-b border-zinc-800 bg-[#121215]">
                    <span id="modalMatkul" class="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Matkul</span>
                    <button onclick="closeModal()" class="text-zinc-500 hover:text-white bg-zinc-800/50 hover:bg-rose-500/20 rounded-md p-1.5 transition-colors">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                
                <div class="p-6 md:p-8 overflow-y-auto custom-scrollbar">
                    <div class="flex flex-wrap items-center gap-3 mb-5">
                        <span id="modalStatus" class="px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest">Status</span>
                        <div class="flex items-center gap-2 text-xs font-medium text-zinc-300 bg-zinc-800/50 px-3 py-1.5 rounded-md border border-zinc-700/50">
                            <svg class="w-3.5 h-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            <span id="modalDeadline">Tenggat Waktu</span>
                        </div>
                    </div>
                    
                    <h2 id="modalJudul" class="text-2xl md:text-3xl font-bold text-zinc-100 mb-6 leading-snug">Judul Tugas</h2>
                    
                    <div class="mb-8">
                        <h4 class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">Instruksi / Deskripsi</h4>
                        <div class="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                            <p id="modalDesc" class="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap"></p>
                        </div>
                    </div>

                    <div id="modalFilesSection" class="hidden">
                        <h4 class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">File Lampiran</h4>
                        <div id="modalFilesList" class="flex flex-col gap-2">
                            </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const tasksData = {json_data_str};
            const modal = document.getElementById('taskModal');
            
            function openModal(index) {{
                const task = tasksData[index];
                
                document.getElementById('modalMatkul').innerText = task.matkul;
                document.getElementById('modalJudul').innerText = task.judul;
                document.getElementById('modalDesc').innerText = task.description || "Tidak ada instruksi khusus.";
                document.getElementById('modalDeadline').innerText = task.deadline;
                
                const isDone = task.status.includes('Selesai');
                const statusEl = document.getElementById('modalStatus');
                statusEl.innerText = task.status.replace("✅ ", "").replace("⚠️ ", "");
                statusEl.className = `px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest ${{isDone ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}}`;

                const filesSection = document.getElementById('modalFilesSection');
                const filesList = document.getElementById('modalFilesList');
                filesList.innerHTML = ''; 
                
                const files = task.file || [];
                
                if (files.length > 0) {{
                    filesSection.classList.remove('hidden');
                    files.forEach(f => {{
                        const fileName = f.file_name || f.file || "Download Lampiran";
                        const fileUrl = f.file || "#";
                        const linkStr = fileUrl.startsWith('http') ? fileUrl : `https://ethol.pens.ac.id/api/upload/tugas/${{fileUrl}}`;

                        filesList.innerHTML += `
                            <a href="${{linkStr}}" target="_blank" class="flex items-center gap-3 p-3.5 rounded-xl bg-[#18181b] border border-zinc-800 hover:border-zinc-600 hover:bg-[#27272a] transition-all group">
                                <div class="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
                                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                                </div>
                                <span class="text-sm font-medium text-zinc-300 group-hover:text-white truncate">${{fileName}}</span>
                            </a>
                        `;
                    }});
                }} else {{
                    filesSection.classList.add('hidden');
                }}

                modal.classList.add('active');
                document.body.style.overflow = 'hidden'; 
            }}

            function closeModal() {{
                modal.classList.remove('active');
                document.body.style.overflow = ''; 
            }}
            
            document.addEventListener('keydown', (e) => {{
                if (e.key === "Escape") closeModal();
            }});
        </script>
    </body>
    </html>
    """
    
    # Simpan HTML ke dalam folder output
    html_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    net_id = "ahmadsyahani06@it.student.pens.ac.id"
    password = "Syahani06"
    
    # Bikin folder otomatis kalau belum ada (buat amannya)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    update_files([]) 

    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--window-size=1920,1080") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3") 
    
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    
    wait = WebDriverWait(driver, 20)

    try:
        print("\n[BACKGROUND MODE AKTIF] Memulai Auto-Sync ETHOL...")
        print(">> [1] Login CAS PENS...")
        driver.get("https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F")
        
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(net_id)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        print(">> [2] Menuju Halaman Tugas...")
        time.sleep(7)
        driver.get("https://ethol.pens.ac.id/mahasiswa/tugas-online")
        
        print(">> [3] Melihat Daftar Tugas")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "v-select__selections")))
        
        driver.execute_script("""
            window.capturedTasks = [];
            const origSend = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.send = function() {
                this.addEventListener('load', function() {
                    try {
                        const data = JSON.parse(this.responseText);
                        if (Array.isArray(data) && data.length > 0 && data[0].hasOwnProperty('title')) {
                            window.capturedTasks = data;
                        }
                    } catch(e) {}
                });
                origSend.apply(this, arguments);
            };
        """)
        
        all_tasks = []

        print(">> Mengambil daftar Matkul...")
        dropdown = driver.find_element(By.CLASS_NAME, "v-select__selections")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", dropdown)
        time.sleep(3) 
        
        # Simpan screenshot ke dalam folder output
        screenshot_path = os.path.join(OUTPUT_DIR, "debug_hantu.png")
        driver.save_screenshot(screenshot_path)
        
        items = driver.find_elements(By.CSS_SELECTOR, ".v-menu__content.menuable__content__active .v-list-item__title")
        matkul_list = []
        
        ignore_words = ["Pilih", "Beranda", "Matakuliah", "Jadwal", "Tugas", "Ujian", "Keluar", "No data"]
        
        for t in items:
            nama_matkul = t.text.strip()
            if nama_matkul and not any(word in nama_matkul for word in ignore_words):
                matkul_list.append(nama_matkul)
                
        matkul_list = list(dict.fromkeys(matkul_list))
        print(f">> Terdeteksi {len(matkul_list)} Mata Kuliah Asli.")

        for matkul in matkul_list:
            print(f">> Cek API: {matkul} ", end="")
            
            driver.execute_script("window.capturedTasks = [];")
            
            dropdown = driver.find_element(By.CLASS_NAME, "v-select__selections")
            driver.execute_script("arguments[0].click();", dropdown)
            time.sleep(1)
            
            menu_items = driver.find_elements(By.CSS_SELECTOR, ".v-menu__content.menuable__content__active .v-list-item")
            for item in menu_items:
                if item.text.strip() == matkul:
                    driver.execute_script("arguments[0].click();", item)
                    break
            
            time.sleep(4)

            tasks_json = driver.execute_script("return window.capturedTasks;")
            
            count = 0
            if tasks_json:
                for item in tasks_json:
                    judul = item.get("title", "")
                    if judul:
                        status = "✅ Selesai" if item.get("submission_time") else "⚠️ Belum Dikerjakan"
                        
                        all_tasks.append({
                            "matkul": matkul,
                            "judul": judul,
                            "description": item.get("description", "Tidak ada deskripsi"),
                            "deadline": item.get("deadline_indonesia", item.get("deadline", "")),
                            "status": status,
                            "file": item.get("file", []),
                            "raw_deadline": item.get("deadline", ""), 
                        })
                        count += 1
            
            print(f"-> Dapet {count} tugas." if count > 0 else "-> Kosong.")
            update_files(all_tasks)

        print("\n>> [4] Memulai Sinkronisasi Google Calendar...")
        sync_calendar(all_tasks)

        print("\n>> [SUCCESS] Selesai Mengambil dan Sinkronisasi Data!")

    except Exception as e:
        print(f"\n!! Waduh Error: {e}")
    finally:
        driver.quit()

def sync_calendar(tasks):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        
        for t in tasks:
            if "Selesai" in t['status'] or not t.get('raw_deadline'):
                continue
            
            iso_time = t['raw_deadline'].replace(" ", "T") + "+07:00"
            
            event = {
              'summary': f"[ETHOL] {t['judul']} - {t['matkul']}",
              'description': f"{t['description']}\n\nStatus: Belum Dikerjakan ⚠️",
              'start': { 'dateTime': iso_time, 'timeZone': 'Asia/Jakarta' },
              'end': { 'dateTime': iso_time, 'timeZone': 'Asia/Jakarta' },
              'reminders': {
                'useDefault': False,
                'overrides': [
                  {'method': 'popup', 'minutes': 24 * 60}, 
                  {'method': 'popup', 'minutes': 120},     
                ],
              },
            }

            events_result = service.events().list(calendarId='primary', q=t['judul']).execute()
            
            if not events_result.get('items', []):
                service.events().insert(calendarId='primary', body=event).execute()
                print(f"   [+] Masuk Kalender: {t['judul']}")
            else:
                print(f"   [~] Udah ada di kalender: {t['judul']}")

    except Exception as e:
        print(f"!! Error sinkronisasi kalender: {e}")

if __name__ == "__main__":
    main()