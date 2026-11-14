# AC Jetta Remake

[English](README.md) | 繁體中文

把你的手機變成 Assetto Corsa 的無線方向盤和腳踏。

手機上顯示觸控方向盤、油門、煞車和按鍵，所有觸控輸入經局域網傳到電腦上的小型 Python 伺服器，再經虛擬 Xbox 360 手柄注入 Windows，遊戲看到的就是一個真的手柄，不需要裝遊戲模組。

```
手機（觸控介面）-- WebSocket，局域網 :9999 --> 電腦伺服器（Python）
    --> vgamepad / ViGEmBus --> 虛擬 Xbox 360 手柄 --> Assetto Corsa
```

2026 年夏天、大學開學之前做的。程式碼在 AI 協助下寫成（Gemini 免費版）；我負責定功能、測試和除錯，前後迭代了五天，Android App 是我自己在 Android Studio 打包的。

## 功能

- **模擬方向盤** — 拖動螢幕上的方向盤，角度會累積計算（atan2 增量，附 ±180° 跨界修正），最大 900°（1.25 圈），鬆手後會自動回正。
- **模擬腳踏** — 油門和煞車分別對應右、左扳機。
- **按鍵** — Start、RB / LB（升檔／降檔）、A 和 Y，對應 Xbox 手柄的相同按鍵。在 Assetto Corsa 的控制設定裡綁定（例如 A 當手煞）。
- **斷線安全鎖** — 手機一斷線，伺服器會即時把搖桿、扳機和所有按鍵歸零，車子不會卡著油門一直衝。
- **自動連接** — 客戶端可以掃描局域網找伺服器，也可以手動輸入電腦 IP。但自動連接還有些未知問題，有時會連不上。
- **極簡協議** — 每幀一個逗號分隔的字串，例如 `X:12345,T:180,B:0,BK:0,ST:0,RB:0,LB:0,A:0,Y:0`。沒有 JSON，熱路徑上不打 log，髒包直接靜默丟掉。

## 檔案結構

```
server/server.py   電腦端：WebSocket 伺服器（端口 9999）+ vgamepad 注入（V23.2）
client/index.html  手機端：整個觸控介面，純 HTML/CSS/JS（V25.0）
                   Android APK 是這個頁面的 WebView 包裝（見 Releases）。
requirements.txt   Python 依賴
```

## 需求

- Windows 10/11 電腦（虛擬手柄需要 ViGEmBus 驅動，只有 Windows 有），並已安裝 Python 3。
- Android 手機，或任何手機瀏覽器，跟電腦在同一個局域網／熱點。
- 電腦上有 Assetto Corsa。
- Assetto Corsa 的 Content Manager。

## 電腦端設定

1. 去 python.org 安裝 Python 3。安裝程式第一個畫面要勾 **Add Python to PATH**，不然 terminal 會找不到 `python` 指令。
2. 去 [Releases](../../releases) 下載 server.py，放到一個你容易找到的資料夾。
3. 在那個資料夾裡開 terminal：

   ```powershell
   pip install vgamepad websockets
   ```

   安裝 `vgamepad` 時會自動彈出 **ViGEmBus 驅動**安裝程式：接受授權、按 Install（需要管理員權限）、再按 Finish。這個驅動就是讓 Windows 以為真的插了一個 Xbox 360 手柄的東西，沒有它，`vgamepad` 就建不出手柄。
4. 啟動伺服器：

   ```powershell
   python (server 檔案的位置)\server.py
   ```

   它會印出你電腦的局域網 IP。這個視窗不要關。
5. 檢查虛擬手柄是不是真的存在：按 Win+R，輸入 `joy.cpl`，按 Enter。應該會看到 "Controller (Xbox 360 Controller for Windows)"。選它、開 Properties，動一下手機方向盤和腳踏，軸應該要有反應。如果沒有手柄出現，就是 ViGEmBus 驅動沒裝好（見下面）。
6. 先開 Assetto Corsa 的 Content Manager，**之後**再啟動伺服器，這樣遊戲啟動時才看得到手柄。如果先開伺服器，有時會跟遊戲連接出問題。失敗的話多試幾次。

如果遇到問題：

- 手機連不上：確認手機和電腦在同一個網絡（同一個 Wi-Fi，或手機熱點、電腦連上去）。在 Windows 防火牆放行 Python，或開放 TCP 端口 9999。
- 出現 `OSError: ViGEmBus is not installed`：去 [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases) 手動安裝驅動並重啟，再啟動伺服器。
- Assetto Corsa 沒反應：關掉遊戲的 Steam Input（Steam 遊戲庫 → 右鍵 Assetto Corsa → Properties → Controller → Disable Steam Input）。Steam 會在遊戲之前攔截 XInput 手柄。

7. 設定做完一次之後，就不用重做第 1、2、3 步了。之後只要找到 server.py、啟動它、看 IP、輸入到手機就能連上。用手柄的時候不要關掉 server.py 那個黑視窗。

## 手機端設定

**方法 A — APK（最簡單）：**去 [Releases](../../releases) 下載 APK、安裝、打開，輸入電腦的局域網 IP（自動連接在某些裝置上用不了，可以試試），就可以開車了。

**方法 B — 瀏覽器：**在手機瀏覽器打開 `client/index.html`（跟電腦同一個網絡），輸入電腦的局域網 IP，就可以開車了，不用安裝。但要先把螢幕轉橫。[Releases](../../releases) ← 這裡也可以下載 `client/index.html`。

注意：自動連接只會掃 `192.168.1.1–254`。如果你的網絡是別的網段（例如手機熱點的 `192.168.43.x`），就手動輸入伺服器印出的 IP。建議直接手動輸入 IP，忽略自動連接功能，因為它大多數時候都不太靈。

## 在 Assetto Corsa 裡綁定控制

伺服器開著、手機連上的狀態下，打開 Assetto Corsa，去 Settings → Controls（Content Manager 是 Settings → Assetto Corsa → Controls）。確認選中的裝置是 Xbox 360 手柄。然後點每一個動作，再動對應的手機控制：

| AC 裡的動作 | 手機控制 | 虛擬輸入 |
|---|---|---|
| Steer Left / Right（轉向） | 拖方向盤 | 左搖桿 X 軸 |
| Gas（油門） | 油門滑桿 | 右扳機 |
| Brake（煞車） | 煞車滑桿 | 左扳機 |
| Shift Up（升檔） | RB 按鍵 | RB |
| Shift Down（降檔） | LB 按鍵 | LB |
| Handbrake（手煞） | A 按鍵 | A |
| （自選） | Y / Start 按鍵 | Y / Start |

如果轉向方向反了，就勾 Invert（反轉）。綁完存一個 preset，下次就不用重做。如果高速時覺得車子太敏感，就調低 Steering Speed 或調高 Speed Sensitivity；如果覺得轉向太遲鈍，就反過來。憑感覺調——可調的是 Steering Speed、Steering Gamma、Filter 和 Speed Sensitivity。

## 已知限制

- V23.2 的伺服器是**單向**的：只接收輸入。
- `BK`（Back 按鍵）永遠是 0——介面上沒有 Back 按鍵。伺服器解析沒問題，只是它永遠不會變成 1。
- 只支援 Windows，因為驅動的原因。
- 在低效能的電腦上表現不好。
- 散熱不好的情況下會讓手機過熱。

## 授權

MIT — 見 [LICENSE](LICENSE)。
