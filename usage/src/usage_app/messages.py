"""Plain Chinese messages for the fixed local-storage/credential error vocabulary."""
MESSAGES = {
    "Newer configuration version; file was preserved": "文件来自较新版本，本版未修改它；请使用相应版本打开。",
    "Unsupported configuration version": "配置版本不兼容，原文件已保留。",
    "Invalid configuration; file was preserved": "配置损坏，原文件已保留；可按说明恢复备份。",
    "Cannot read configuration": "无法读取配置，请检查文件权限或占用情况。",
    "Save failed; previous configuration was preserved": "保存失败，原配置已保留；请检查文件权限或占用情况。",
    "Recovery failed; files were preserved": "备份恢复失败，文件已保留，请稍后重试。",
    "Invalid desktop settings; configuration was preserved": "显示设置损坏，原配置已保留。",
    "Invalid account configuration; file was preserved": "账号配置损坏，原文件已保留。",
    "Invalid cached snapshot; file was preserved": "缓存损坏，原文件已保留；重新查询后更新。",
    "Invalid snapshot cache; file was preserved": "缓存损坏，原文件已保留；重新查询后更新。",
    "Secure credential read failed": "无法读取 Windows 凭据，请检查当前用户的凭据权限。",
    "Secure credential write failed": "密钥未能保存到 Windows 凭据，原账号保持不变。",
    "Secure credential save failed": "密钥未能保存到 Windows 凭据，原账号保持不变。",
    "Secure credential deletion failed": "本机旧密钥未能清理，请稍后重试。",
    "Secure credential delete failed": "本机旧密钥未能清理，请稍后重试。",
    "Secure credential removal failed": "本机旧密钥未能清理，请稍后重试。",
    "Existing instance did not confirm restore; no second instance was started": "正在运行的usage未能回应，请稍后重试。",
    "Another instance is starting; please retry": "usage正在启动，请稍后重试。",
    "User data directory unavailable": "无法找到本机用户数据目录，请检查 Windows 用户环境。",
    "Invalid credential value": "API Key 为空、过长或含换行，请检查后重试。",
    "Invalid stored credential": "本机密钥无法读取，请重新配置。",
    "Invalid credential size": "本机密钥格式不正确，请重新配置。",
    "Invalid application credential reference": "本机凭据引用不正确，原配置已保留。",
}


def product_message(value: str | Exception) -> str:
    message = str(value)
    if message in MESSAGES:
        return MESSAGES[message]
    if any("\u4e00" <= char <= "\u9fff" for char in message):
        return message
    return "操作未完成，请稍后重试。原有数据已保留。"
