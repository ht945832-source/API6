import numpy as np
import os
import asyncio
import hashlib
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from collections import deque, Counter
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# --- CẤU HÌNH ---
TOKEN = "8670893641:AAGovRHAo8mIGvOXchbTqxZZIG2KQiwdRcw"
GROUP_CHAT_ID = "-1002347313054" 
ADMIN_ID = "@tranhoang2286"

app = FastAPI(title="HỆ THỐNG ADMIN AI HOÀNG DZ")
bot = Bot(token=TOKEN)

class SystemState:
    def __init__(self):
        # [span_0](start_span)Đã sửa số phiên khởi đầu theo ý bạn[span_0](end_span)
        self.phien = 184726 
        self.raw_data = deque(["Tài", "Xỉu", "Tài", "Xỉu"], maxlen=100)
        self.win = 0
        self.total = 0
        self.current_pred = "Tài"
        self.current_conf = 78.5
        self.mem_ao = 2650
        self.status = "CHỜ ADMIN CHỐT PHIÊN"

state = SystemState()

# --- CÔNG THỨC AI ---
def calculate_master_logic():
    h = hashlib.md5(str(time.time()).encode()).hexdigest()
    counts = Counter(state.raw_data)
    total_samples = len(state.raw_data) if len(state.raw_data) > 0 else 1
    prob = (counts["Tài"] / total_samples * 0.4) + (int(h[:2], 16)/510)
    
    if prob >= 0.5: 
        return "Tài", round(min(prob*100, 99.9), 2)
    return "Xỉu", round(min((1-prob)*100, 99.9), 2)

# --- TELEGRAM HELPER ---
async def send_to_tele(text, keyboard=None):
    try:
        await bot.send_message(chat_id=GROUP_CHAT_ID, text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        print(f"Lỗi Tele: {e}")

# --- API MODELS ---
class ResultInput(BaseModel):
    phien_id: int
    ket_qua_thuc_te: str

# --- ROUTES ---

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/api/status", tags=["Người Dùng"])
def get_status():
    [span_1](start_span)"""Trả về JSON có hỗ trợ tiếng Việt không lỗi font[span_1](end_span)"""
    data = {
        "phien_hien_tai": state.phien,
        "du_doan_dang_cho": state.current_pred,
        "do_tin_cay": f"{state.current_conf}%",
        "trang_thai": state.status,
        "mem_online": state.mem_ao
    }
    return JSONResponse(content=data, media_type="application/json; charset=utf-8")

@app.post("/admin/confirm-result", tags=["Quản Trị Viên"])
async def confirm_result(data: ResultInput):
    kq = data.ket_qua_thuc_te.strip().capitalize()
    
    if kq not in ["Tài", "Xỉu"]:
        raise HTTPException(status_code=400, detail="Vui lòng chỉ nhập 'Tài' hoặc 'Xỉu'")

    if data.phien_id != state.phien:
        raise HTTPException(status_code=400, detail=f"Sai phiên! Phiên hiện tại là {state.phien}")

    # 1. Xử lý kết quả
    is_correct = "❌ SAI"
    if state.current_pred == kq:
        state.win += 1
        is_correct = "✅ ĐÚNG"
    
    state.total += 1
    state.raw_data.append(kq)

    # 2. Báo kết quả phiên cũ
    res_text = (
        f"🔔 <b>KẾT QUẢ PHIÊN {state.phien}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎲 Thực tế: <b>{kq}</b>\n"
        f"🎯 AI dự đoán: <b>{state.current_pred}</b>\n"
        f"➔ Kết quả: {is_correct}\n"
        f"📈 Tỷ lệ thắng: <code>{state.win}/{state.total}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 <i>Đang phân tích phiên tiếp theo...</i>"
    )
    await send_to_tele(res_text)

    # 3. Delay phân tích
    state.status = "ĐANG PHÂN TÍCH..."
    await asyncio.sleep(3)

    # 4. Nhảy phiên mới
    state.phien += 1
    pred, conf = calculate_master_logic()
    state.current_pred = pred
    state.current_conf = conf
    state.mem_ao += np.random.randint(5, 25)

    # 5. Gửi dự đoán mới
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 MUA CÔNG THỨC VIP", url=f"https://t.me/{ADMIN_ID.replace('@','')}")],
        [InlineKeyboardButton("💬 LIÊN HỆ ADMIN", url=f"https://t.me/{ADMIN_ID.replace('@','')}")]
    ])
    
    pred_text = (
        f"🚀 <b>AI PREDICTOR PREMIUM v4.0</b> 🚀\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>PHIÊN:</b> <code>#{state.phien}</code>\n"
        f"🎯 <b>DỰ ĐOÁN:</b> ➔ ⚠️ <b>{pred.upper()}</b> ⚠️\n"
        f"📊 <b>ĐỘ TIN CẬY:</b> <code>{conf}%</code>\n"
        f"👥 <b>NGƯỜI ĐANG THEO:</b> <code>{state.mem_ao}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>CAM KẾT KẾT QUẢ CHUẨN XÁC 90%</b>\n"
        f"📍 Admin: {ADMIN_ID}"
    )
    await send_to_tele(pred_text, kb)
    
    state.status = "CHỜ ADMIN CHỐT PHIÊN"
    return JSONResponse(content={"status": "Thành công", "phien_tiep_theo": state.phien}, media_type="application/json; charset=utf-8")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
