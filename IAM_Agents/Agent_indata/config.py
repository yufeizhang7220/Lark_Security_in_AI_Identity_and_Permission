LLM_CONFIG = {
    "api_key": "ark-d61ab9da-a6f4-4a5e-94b3-c1ca9c4874eb-0f8ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "ep-20260423223132-gxqgd"
}

AGENT_ID = "Agent_indata"
HOST = "localhost"
PORT = 8787

IAM_CONFIG = {
    "identity_registration_url": "http://localhost:9002/IAMsystem/identity/register/bot",
    "identity_verify_url": "http://localhost:9002/IAMsystem/identity/verify",
    "auth_apply_token_url": "http://localhost:9001/IAMsystem/auth/apply-token",
    "auth_verify_token_url": "http://localhost:9001/IAMsystem/auth/verify-token",
    "auth_revoke_token_url": "http://localhost:9001/IAMsystem/auth/revoke-token",
    "storage_dir": "Storage",
    "reg_info_file": "Storage/IMA_reg_info.json",
    "access_tokens_file": "Storage/AccessTokens.json"
}

DEFAULT_BOT_SCOPE = {
    "indata": ["read_contact", "read_calendar", "read_bitable"],
    "doc": ["read"],
    "iam": ["verify_token"]
}
