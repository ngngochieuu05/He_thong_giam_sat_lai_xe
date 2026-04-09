-- ============================================================
-- He_Thong_Giam_Sat_Lai_Xe - DATABASE SCRIPT (ASCII safe)
-- Database: He_Thong_Giam_Sat_Lai_Xe_LGBT
-- Server  : TEDDY\SQLEXPRESS
-- Date    : 2026-03-27
-- ============================================================

USE master;
GO


IF EXISTS (SELECT name FROM sys.databases WHERE name = N'He_Thong_Giam_Sat_Lai_Xe_LGBT')
BEGIN
    ALTER DATABASE He_Thong_Giam_Sat_Lai_Xe_LGBT SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE He_Thong_Giam_Sat_Lai_Xe_LGBT;
END
GO

CREATE DATABASE He_Thong_Giam_Sat_Lai_Xe_LGBT COLLATE Vietnamese_CI_AS;
GO

USE He_Thong_Giam_Sat_Lai_Xe_LGBT;
GO

-- ============================================================
-- TABLE 1: Admin_Accounts
-- ============================================================
CREATE TABLE Admin_Accounts (
    admin_id    INT          IDENTITY(1,1) PRIMARY KEY,
    username    NVARCHAR(100) NOT NULL UNIQUE,
    password    NVARCHAR(255) NOT NULL,
    name        NVARCHAR(200) NOT NULL,
    is_active   BIT           NOT NULL DEFAULT 1,
    created_at  DATETIME      NOT NULL DEFAULT GETDATE(),
    updated_at  DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================
-- TABLE 2: Tai_Xe (Driver accounts)
-- Mirrors: accounts.json -> user_accounts[]
-- Fields : driver_id, username, name, password,
--          telegram_chat_id, plan, weather_api_key, avatar
-- ============================================================
CREATE TABLE Tai_Xe (
    tai_xe_id        INT           IDENTITY(1,1) PRIMARY KEY,
    driver_id        NVARCHAR(20)  NOT NULL UNIQUE,
    username         NVARCHAR(100) NOT NULL UNIQUE,
    name             NVARCHAR(200) NOT NULL,
    password         NVARCHAR(255) NOT NULL,
    telegram_chat_id NVARCHAR(50)  NULL,
    goi_dich_vu      NVARCHAR(20)  NOT NULL DEFAULT 'Free'
                     CHECK (goi_dich_vu IN ('Free','Pro')),
    weather_api_key  NVARCHAR(500) NULL,
    avatar           NVARCHAR(500) NULL,
    is_active        BIT           NOT NULL DEFAULT 1,
    created_at       DATETIME      NOT NULL DEFAULT GETDATE(),
    updated_at       DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================
-- TABLE 3: Telegram_Lien_Ket
-- Mirrors: accounts.json -> user_accounts[].telegram_data
-- ============================================================
CREATE TABLE Telegram_Lien_Ket (
    lien_ket_id       INT           IDENTITY(1,1) PRIMARY KEY,
    tai_xe_id         INT           NOT NULL,
    chat_id           NVARCHAR(50)  NOT NULL,
    telegram_username NVARCHAR(100) NULL,
    linked_at         DATETIME      NOT NULL DEFAULT GETDATE(),
    is_active         BIT           NOT NULL DEFAULT 1,

    CONSTRAINT FK_TelegramLienKet_TaiXe
        FOREIGN KEY (tai_xe_id) REFERENCES Tai_Xe(tai_xe_id) ON DELETE CASCADE
);
GO
CREATE INDEX IX_TelegramLienKet_TaiXeId ON Telegram_Lien_Ket(tai_xe_id);
GO

-- ============================================================
-- TABLE 4: Telegram_Tokens
-- Mirrors: BUS/oa_core/data/telegram_tokens.json
-- ============================================================
CREATE TABLE Telegram_Tokens (
    token_id   INT          IDENTITY(1,1) PRIMARY KEY,
    token      NVARCHAR(50) NOT NULL UNIQUE,
    username   NVARCHAR(100) NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT GETDATE(),
    expires_at DATETIME     NOT NULL,
    is_used    BIT          NOT NULL DEFAULT 0
);
GO
CREATE INDEX IX_TelegramTokens_Token    ON Telegram_Tokens(token);
CREATE INDEX IX_TelegramTokens_Username ON Telegram_Tokens(username);
GO

-- ============================================================
-- TABLE 5: Dang_Nhap_Lich_Su (Login history)
-- Mirrors: dashboard_data.json -> users.{u}.login_history[]
-- ============================================================
CREATE TABLE Dang_Nhap_Lich_Su (
    dang_nhap_id INT      IDENTITY(1,1) PRIMARY KEY,
    tai_xe_id    INT      NOT NULL,
    login_date   DATE     NOT NULL,
    login_time   TIME     NOT NULL,
    created_at   DATETIME NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_DangNhapLichSu_TaiXe
        FOREIGN KEY (tai_xe_id) REFERENCES Tai_Xe(tai_xe_id) ON DELETE CASCADE
);
GO
CREATE INDEX IX_DangNhapLichSu_TaiXeId ON Dang_Nhap_Lich_Su(tai_xe_id);
CREATE INDEX IX_DangNhapLichSu_Date    ON Dang_Nhap_Lich_Su(login_date);
GO

-- ============================================================
-- TABLE 6: Phien_Lai (Driving sessions)
-- Mirrors: dashboard_data.json -> users.{u}.driving_sessions[]
-- ============================================================
CREATE TABLE Phien_Lai (
    phien_lai_id     INT      IDENTITY(1,1) PRIMARY KEY,
    tai_xe_id        INT      NOT NULL,
    session_date     DATE     NOT NULL,
    duration_minutes INT      NOT NULL DEFAULT 0 CHECK (duration_minutes >= 0),
    so_vi_pham       INT      NOT NULL DEFAULT 0 CHECK (so_vi_pham >= 0),
    created_at       DATETIME NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_PhienLai_TaiXe
        FOREIGN KEY (tai_xe_id) REFERENCES Tai_Xe(tai_xe_id) ON DELETE CASCADE
);
GO
CREATE INDEX IX_PhienLai_TaiXeId ON Phien_Lai(tai_xe_id);
CREATE INDEX IX_PhienLai_Date    ON Phien_Lai(session_date);
GO

-- ============================================================
-- TABLE 7: Canh_Bao_Thong_Ke (Daily alert statistics)
-- Mirrors: dashboard_data.json -> users.{u}.daily_alerts{}
-- ============================================================
CREATE TABLE Canh_Bao_Thong_Ke (
    thong_ke_id      INT      IDENTITY(1,1) PRIMARY KEY,
    tai_xe_id        INT      NOT NULL,
    alert_date       DATE     NOT NULL,
    so_canh_bao_ngay INT      NOT NULL DEFAULT 0,

    CONSTRAINT FK_CanhBaoThongKe_TaiXe
        FOREIGN KEY (tai_xe_id) REFERENCES Tai_Xe(tai_xe_id) ON DELETE CASCADE,
    CONSTRAINT UQ_CanhBaoThongKe_TaiXe_Date
        UNIQUE (tai_xe_id, alert_date)
);
GO
CREATE INDEX IX_CanhBaoThongKe_TaiXeId ON Canh_Bao_Thong_Ke(tai_xe_id);
CREATE INDEX IX_CanhBaoThongKe_Date    ON Canh_Bao_Thong_Ke(alert_date);
GO

-- ============================================================
-- TABLE 8: Tong_Ket_Tai_Xe (Driver summary stats)
-- Mirrors: dashboard_data.json -> users.{u}.total_alerts/total_km/safety_score
-- ============================================================
CREATE TABLE Tong_Ket_Tai_Xe (
    tong_ket_id   INT      IDENTITY(1,1) PRIMARY KEY,
    tai_xe_id     INT      NOT NULL UNIQUE,
    tong_canh_bao INT      NOT NULL DEFAULT 0,
    tong_km       FLOAT    NOT NULL DEFAULT 0.0,
    diem_an_toan  INT      NOT NULL DEFAULT 100 CHECK (diem_an_toan BETWEEN 0 AND 100),
    cap_nhat_luc  DATETIME NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_TongKetTaiXe_TaiXe
        FOREIGN KEY (tai_xe_id) REFERENCES Tai_Xe(tai_xe_id) ON DELETE CASCADE
);
GO

-- ============================================================
-- TABLE 9: Thong_Bao_Log (Telegram notification logs)
-- Mirrors: BUS/oa_core/data/thong_bao_log.json -> logs[]
-- ============================================================
CREATE TABLE Thong_Bao_Log (
    log_id        INT           IDENTITY(1,1) PRIMARY KEY,
    log_time      NVARCHAR(30)  NOT NULL,
    chat_id       NVARCHAR(50)  NOT NULL,
    content       NVARCHAR(MAX) NOT NULL,
    trang_thai    NVARCHAR(20)  NOT NULL DEFAULT 'fail'
                  CHECK (trang_thai IN ('success','fail')),
    error_message NVARCHAR(500) NULL,
    created_at    DATETIME      NOT NULL DEFAULT GETDATE()
);
GO
CREATE INDEX IX_ThongBaoLog_ChatId    ON Thong_Bao_Log(chat_id);
CREATE INDEX IX_ThongBaoLog_TrangThai ON Thong_Bao_Log(trang_thai);
GO

-- ============================================================
-- TABLE 10: Cau_Hinh_He_Thong (System configuration)
-- Mirrors: BUS/oa_core/data/API.json  +  GUI/data/model_config.json
-- ============================================================
CREATE TABLE Cau_Hinh_He_Thong (
    cau_hinh_id   INT           IDENTITY(1,1) PRIMARY KEY,
    config_key    NVARCHAR(100) NOT NULL UNIQUE,
    config_value  NVARCHAR(MAX) NULL,
    description   NVARCHAR(500) NULL,
    updated_at    DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================
-- SEED DATA
-- ============================================================

-- System config
INSERT INTO Cau_Hinh_He_Thong (config_key, config_value, description) VALUES
('telegram_bot_token',    '',                    'Telegram bot token'),
('telegram_chat_id',      '',                    'Default alert chat ID'),
('telegram_bot_name',     'safedrive_alert_bot', 'Telegram bot username'),
('camera_default_index',  '0',                   'Default camera index'),
('app_version',           'v1.0.0',              'Application version'),
('max_log_records',       '700',                 'Max log records to keep');
GO

-- Admin account (from accounts.json)
INSERT INTO Admin_Accounts (username, password, name) VALUES
('admin', 'admin', N'Quan tri vien he thong');
GO

-- Sample drivers (from accounts.json -> user_accounts)
INSERT INTO Tai_Xe (driver_id, username, name, password, goi_dich_vu) VALUES
('TX001', 'user01',   N'Nguyen Van An',   'user01', 'Free'),
('TX002', 'taixe02',  N'Tran Thi Binh',   'user02', 'Free'),
('TX003', 'driver03', N'Le Van Cuong',     'user03', 'Pro');
GO

-- Init summary stats for all drivers
INSERT INTO Tong_Ket_Tai_Xe (tai_xe_id, tong_canh_bao, tong_km, diem_an_toan)
SELECT tai_xe_id, 0, 0.0, 100 FROM Tai_Xe;
GO

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

-- SP1: Driver login + record history
CREATE OR ALTER PROCEDURE sp_DangNhap_TaiXe
    @username NVARCHAR(100),
    @password NVARCHAR(255),
    @ket_qua  INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @tai_xe_id INT;
    SELECT @tai_xe_id = tai_xe_id FROM Tai_Xe
    WHERE username = @username AND password = @password AND is_active = 1;

    IF @tai_xe_id IS NOT NULL
    BEGIN
        SET @ket_qua = 1;
        INSERT INTO Dang_Nhap_Lich_Su (tai_xe_id, login_date, login_time)
        VALUES (@tai_xe_id, CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME));
    END
    ELSE SET @ket_qua = 0;
END;
GO

-- SP2: Admin login
CREATE OR ALTER PROCEDURE sp_DangNhap_Admin
    @username NVARCHAR(100),
    @password NVARCHAR(255),
    @ket_qua  INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @cnt INT;
    SELECT @cnt = COUNT(1) FROM Admin_Accounts
    WHERE username = @username AND password = @password AND is_active = 1;
    SET @ket_qua = CASE WHEN @cnt > 0 THEN 1 ELSE 0 END;
END;
GO

-- SP3: Get full driver info by username
CREATE OR ALTER PROCEDURE sp_LayThongTin_TaiXe
    @username NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT tx.tai_xe_id, tx.driver_id, tx.username, tx.name, tx.goi_dich_vu AS goi_dich_vu,
           tx.weather_api_key, tx.avatar,
           tlk.chat_id           AS telegram_chat_id,
           tlk.telegram_username,
           tlk.linked_at         AS telegram_linked_at,
           tkt.diem_an_toan      AS safety_score,
           tkt.tong_canh_bao     AS total_alerts,
           tkt.tong_km           AS total_km
    FROM Tai_Xe tx
    LEFT JOIN Telegram_Lien_Ket  tlk ON tlk.tai_xe_id = tx.tai_xe_id AND tlk.is_active = 1
    LEFT JOIN Tong_Ket_Tai_Xe    tkt ON tkt.tai_xe_id = tx.tai_xe_id
    WHERE tx.username = @username AND tx.is_active = 1;
END;
GO

-- SP4: Save driving session
CREATE OR ALTER PROCEDURE sp_Them_PhienLai
    @username           NVARCHAR(100),
    @session_date       DATE,
    @duration_minutes   INT,
    @so_vi_pham         INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @tai_xe_id INT;
    SELECT @tai_xe_id = tai_xe_id FROM Tai_Xe WHERE username = @username;
    IF @tai_xe_id IS NOT NULL
    BEGIN
        INSERT INTO Phien_Lai (tai_xe_id, session_date, duration_minutes, so_vi_pham)
        VALUES (@tai_xe_id, @session_date, @duration_minutes, @so_vi_pham);

        IF @so_vi_pham > 0
            UPDATE Tong_Ket_Tai_Xe
            SET tong_canh_bao = tong_canh_bao + @so_vi_pham,
                diem_an_toan  = CASE WHEN (diem_an_toan - @so_vi_pham) < 0 THEN 0
                                     ELSE (diem_an_toan - @so_vi_pham) END,
                cap_nhat_luc  = GETDATE()
            WHERE tai_xe_id = @tai_xe_id;
    END
END;
GO

-- SP5: Record an alert (daily_alerts + total_alerts)
CREATE OR ALTER PROCEDURE sp_Ghi_CanhBao
    @username   NVARCHAR(100),
    @alert_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @alert_date IS NULL SET @alert_date = CAST(GETDATE() AS DATE);
    DECLARE @tai_xe_id INT;
    SELECT @tai_xe_id = tai_xe_id FROM Tai_Xe WHERE username = @username;

    IF @tai_xe_id IS NOT NULL
    BEGIN
        MERGE Canh_Bao_Thong_Ke AS T
        USING (SELECT @tai_xe_id tai_xe_id, @alert_date alert_date) AS S
            ON T.tai_xe_id = S.tai_xe_id AND T.alert_date = S.alert_date
        WHEN MATCHED     THEN UPDATE SET so_canh_bao_ngay = so_canh_bao_ngay + 1
        WHEN NOT MATCHED THEN INSERT (tai_xe_id, alert_date, so_canh_bao_ngay)
                              VALUES (S.tai_xe_id, S.alert_date, 1);

        UPDATE Tong_Ket_Tai_Xe
        SET tong_canh_bao = tong_canh_bao + 1, cap_nhat_luc = GETDATE()
        WHERE tai_xe_id = @tai_xe_id;
    END
END;
GO

-- SP6: Save Telegram notification log
CREATE OR ALTER PROCEDURE sp_Luu_ThongBaoLog
    @log_time       NVARCHAR(30),
    @chat_id        NVARCHAR(50),
    @content        NVARCHAR(MAX),
    @trang_thai     NVARCHAR(20),
    @error_message  NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Thong_Bao_Log (log_time, chat_id, content, trang_thai, error_message)
    VALUES (@log_time, @chat_id, @content, @trang_thai, @error_message);

    -- Keep max 700 records
    DELETE FROM Thong_Bao_Log
    WHERE log_id NOT IN (SELECT TOP 700 log_id FROM Thong_Bao_Log ORDER BY log_id DESC);
END;
GO

-- SP7: Get all drivers list (Admin page)
CREATE OR ALTER PROCEDURE sp_LayDanhSach_TaiXe
AS
BEGIN
    SET NOCOUNT ON;
    SELECT tx.tai_xe_id, tx.driver_id, tx.username, tx.name, tx.goi_dich_vu,
           tx.is_active, tx.created_at,
           tlk.chat_id AS telegram_chat_id, tlk.telegram_username,
           tkt.diem_an_toan AS safety_score, tkt.tong_canh_bao AS total_alerts
    FROM Tai_Xe tx
    LEFT JOIN Telegram_Lien_Ket  tlk ON tlk.tai_xe_id = tx.tai_xe_id AND tlk.is_active = 1
    LEFT JOIN Tong_Ket_Tai_Xe    tkt ON tkt.tai_xe_id = tx.tai_xe_id
    ORDER BY tx.driver_id;
END;
GO

-- SP8: Get all sessions (Admin page - Phien Lai)
CREATE OR ALTER PROCEDURE sp_LayPhienLai_Admin
AS
BEGIN
    SET NOCOUNT ON;
    SELECT tx.username, tx.name,
           pl.session_date, pl.duration_minutes, pl.so_vi_pham,
           tkt.diem_an_toan, pl.phien_lai_id
    FROM Phien_Lai pl
    JOIN  Tai_Xe          tx  ON tx.tai_xe_id  = pl.tai_xe_id
    LEFT JOIN Tong_Ket_Tai_Xe tkt ON tkt.tai_xe_id = pl.tai_xe_id
    ORDER BY pl.session_date DESC, pl.phien_lai_id DESC;
END;
GO

-- SP9: Link Telegram to driver
CREATE OR ALTER PROCEDURE sp_LienKet_Telegram
    @username           NVARCHAR(100),
    @chat_id            NVARCHAR(50),
    @telegram_username  NVARCHAR(100) = NULL,
    @ket_qua            INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @tai_xe_id INT;
    SELECT @tai_xe_id = tai_xe_id FROM Tai_Xe WHERE username = @username;
    IF @tai_xe_id IS NULL  BEGIN SET @ket_qua = 0; RETURN; END
    IF EXISTS (SELECT 1 FROM Telegram_Lien_Ket WHERE tai_xe_id = @tai_xe_id AND is_active = 1)
        BEGIN SET @ket_qua = -1; RETURN; END

    INSERT INTO Telegram_Lien_Ket (tai_xe_id, chat_id, telegram_username)
    VALUES (@tai_xe_id, @chat_id, @telegram_username);

    UPDATE Tai_Xe SET telegram_chat_id = @chat_id, updated_at = GETDATE()
    WHERE tai_xe_id = @tai_xe_id;
    SET @ket_qua = 1;
END;
GO

-- SP10: Login + session history for user (Lich Su page)
CREATE OR ALTER PROCEDURE sp_LichSu_TaiXe
    @username NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @tai_xe_id INT;
    SELECT @tai_xe_id = tai_xe_id FROM Tai_Xe WHERE username = @username;

    SELECT CONVERT(NVARCHAR(10), login_date, 23) AS ngay,
           CONVERT(NVARCHAR(8),  login_time, 108) AS gio
    FROM   Dang_Nhap_Lich_Su
    WHERE  tai_xe_id = @tai_xe_id
    ORDER  BY login_date DESC, login_time DESC;

    SELECT CONVERT(NVARCHAR(10), session_date, 23) AS ngay,
           duration_minutes, so_vi_pham
    FROM   Phien_Lai
    WHERE  tai_xe_id = @tai_xe_id
    ORDER  BY session_date DESC;
END;
GO

-- SP11: Dashboard stats for user
CREATE OR ALTER PROCEDURE sp_Dashboard_TaiXe
    @username NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @tai_xe_id INT;
    SELECT @tai_xe_id = tai_xe_id FROM Tai_Xe WHERE username = @username;

    SELECT tong_canh_bao, tong_km, diem_an_toan
    FROM   Tong_Ket_Tai_Xe WHERE tai_xe_id = @tai_xe_id;

    SELECT COUNT(1) AS today_logins
    FROM   Dang_Nhap_Lich_Su
    WHERE  tai_xe_id = @tai_xe_id AND login_date = CAST(GETDATE() AS DATE);

    SELECT ISNULL(SUM(duration_minutes), 0) AS today_drive_minutes
    FROM   Phien_Lai
    WHERE  tai_xe_id = @tai_xe_id AND session_date = CAST(GETDATE() AS DATE);

    SELECT ISNULL(so_canh_bao_ngay, 0) AS today_alerts
    FROM   Canh_Bao_Thong_Ke
    WHERE  tai_xe_id = @tai_xe_id AND alert_date = CAST(GETDATE() AS DATE);
END;
GO

-- ============================================================
-- VIEWS
-- ============================================================
CREATE OR ALTER VIEW vw_ThongTin_TaiXe_DayDu AS
SELECT tx.tai_xe_id, tx.driver_id, tx.username, tx.name, tx.password,
       tx.goi_dich_vu, tx.telegram_chat_id, tx.weather_api_key, tx.avatar, tx.is_active,
       tlk.chat_id AS tele_chat_id, tlk.telegram_username, tlk.linked_at AS telegram_linked_at,
       tkt.diem_an_toan AS safety_score, tkt.tong_canh_bao AS total_alerts, tkt.tong_km AS total_km
FROM   Tai_Xe tx
LEFT JOIN Telegram_Lien_Ket tlk ON tlk.tai_xe_id = tx.tai_xe_id AND tlk.is_active = 1
LEFT JOIN Tong_Ket_Tai_Xe   tkt ON tkt.tai_xe_id = tx.tai_xe_id;
GO

CREATE OR ALTER VIEW vw_PhienLai_Admin AS
SELECT tx.username, tx.name AS ten_tai_xe, tx.driver_id,
       pl.phien_lai_id, pl.session_date, pl.duration_minutes, pl.so_vi_pham,
       tkt.diem_an_toan
FROM   Phien_Lai pl
JOIN   Tai_Xe          tx  ON tx.tai_xe_id  = pl.tai_xe_id
LEFT JOIN Tong_Ket_Tai_Xe tkt ON tkt.tai_xe_id = pl.tai_xe_id;
GO

PRINT 'Database He_Thong_Giam_Sat_Lai_Xe_LGBT created successfully.';
PRINT '  - 10 Tables';
PRINT '  - 11 Stored Procedures';
PRINT '  - 2 Views';
GO
