-- ============================================================
-- 迁移脚本 003：新增接口测试模块（interfaces / interface_test_cases）
-- 适用：已有数据库升级（执行一次；重复执行会因表已存在而报错）
-- ============================================================

CREATE TABLE `interfaces` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '接口ID',
  `project_id` BIGINT NOT NULL COMMENT '所属项目ID',
  `name` VARCHAR(200) NOT NULL COMMENT '接口名称',
  `method` VARCHAR(10) NOT NULL DEFAULT 'GET' COMMENT '请求方法：GET/POST/PUT/DELETE',
  `path` VARCHAR(500) NOT NULL COMMENT '接口路径',
  `summary` VARCHAR(500) DEFAULT NULL COMMENT '接口描述',
  `headers` TEXT DEFAULT NULL COMMENT '请求头（JSON）',
  `params` TEXT DEFAULT NULL COMMENT '查询参数（JSON 数组）',
  `body` TEXT DEFAULT NULL COMMENT '请求体（JSON）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_interface_project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接口定义表';

CREATE TABLE `interface_test_cases` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '接口用例ID',
  `project_id` BIGINT NOT NULL COMMENT '所属项目ID',
  `interface_id` BIGINT DEFAULT NULL COMMENT '来源接口ID',
  `case_no` VARCHAR(20) NOT NULL COMMENT '用例编号（API0001）',
  `title` VARCHAR(200) NOT NULL COMMENT '用例标题',
  `category` VARCHAR(50) NOT NULL DEFAULT 'normal' COMMENT '类别：normal/exception/boundary/security/parameter',
  `method` VARCHAR(10) NOT NULL DEFAULT 'GET' COMMENT '请求方法',
  `path` VARCHAR(500) NOT NULL COMMENT '请求路径',
  `test_data` TEXT DEFAULT NULL COMMENT '测试数据',
  `request_payload` TEXT DEFAULT NULL COMMENT '请求参数/请求体',
  `expected_status` VARCHAR(50) DEFAULT NULL COMMENT '预期状态码',
  `expected_result` TEXT DEFAULT NULL COMMENT '预期结果',
  `priority` VARCHAR(10) NOT NULL DEFAULT '中' COMMENT '优先级：高/中/低',
  `preconditions` TEXT DEFAULT NULL COMMENT '前置条件',
  `steps` TEXT DEFAULT NULL COMMENT '测试步骤',
  `remark` TEXT DEFAULT NULL COMMENT '备注',
  `status` VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '状态',
  `created_by` BIGINT DEFAULT NULL COMMENT '创建人',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_interface_case_project` (`project_id`),
  KEY `idx_interface_case_interface` (`interface_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接口测试用例表';
