-- 培训专用管理员：train（截图手册用）
-- 密码明文 66668888 —— worker 登录时会自动升级为哈希（与初始密码机制一致）
INSERT INTO users (username, password, real_name, role, status, position)
VALUES ('train', '66668888', 'Train', 'user', 'active', '副总经理');
-- 权限与数据范围完全复制 tom（完整管理员视图）
UPDATE users SET perms=(SELECT perms FROM users WHERE username='tom') WHERE username='train';
UPDATE users SET vis_can_see_me=(SELECT vis_can_see_me FROM users WHERE username='tom') WHERE username='train';
UPDATE users SET vis_he_can_see=(SELECT vis_he_can_see FROM users WHERE username='tom') WHERE username='train';
-- 管理员名单（免审批直达）
INSERT OR IGNORE INTO managers (username) VALUES ('train');
