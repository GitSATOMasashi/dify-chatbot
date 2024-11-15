-- ユーザーのトークン使用量テーブル
CREATE TABLE user_token_usage (
    user_id VARCHAR(255),
    date DATE,
    tokens_used INTEGER,
    PRIMARY KEY (user_id, date)
);

-- ユーザーの制限設定テーブル
CREATE TABLE user_token_limits (
    user_id VARCHAR(255) PRIMARY KEY,
    daily_limit INTEGER DEFAULT 1000
); 