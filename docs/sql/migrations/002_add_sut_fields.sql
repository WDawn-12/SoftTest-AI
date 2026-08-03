-- ============================================================
-- 迁移脚本 002：projects 表新增被测系统（SUT）字段
-- 适用：已有数据库升级（执行一次；重复执行会因列已存在而报错）
-- ============================================================
ALTER TABLE `projects`
  ADD COLUMN `system_name` VARCHAR(100) DEFAULT NULL COMMENT '被测系统名称' AFTER `owner_id`,
  ADD COLUMN `test_url` VARCHAR(500) DEFAULT NULL COMMENT '测试网址' AFTER `system_name`,
  ADD COLUMN `system_type` VARCHAR(20) DEFAULT NULL COMMENT '系统类型：Web后台/Web网站/微信小程序/Android/iOS' AFTER `test_url`,
  ADD COLUMN `browser_type` VARCHAR(20) DEFAULT NULL COMMENT '浏览器类型：Chrome/Edge/Firefox' AFTER `system_type`,
  ADD COLUMN `login_username` VARCHAR(100) DEFAULT NULL COMMENT '测试账号' AFTER `browser_type`,
  ADD COLUMN `login_password` VARCHAR(255) DEFAULT NULL COMMENT '测试密码（加密存储）' AFTER `login_username`,
  ADD COLUMN `system_description` TEXT DEFAULT NULL COMMENT '系统描述' AFTER `login_password`;
