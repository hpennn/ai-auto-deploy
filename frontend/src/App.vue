<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="logoClickCount++">
        <span class="logo">🚀</span>
        <h1>AI Auto Deploy</h1>
        <span class="version">v1.2</span>
      </div>
      <div class="header-right">
        <div class="tab-bar">
          <button class="tab-btn" :class="{ active: activeTab === 'deploy' }" @click="activeTab = 'deploy'">
            📦 部署
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'generate' }" @click="activeTab = 'generate'">
            ✨ 生成项目
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'fix' }" @click="activeTab = 'fix'">
            🔧 代码检测
          </button>
          <button v-if="isAdmin" class="tab-btn admin-tab" :class="{ active: activeTab === 'admin' }" @click="activeTab = 'admin'">
            🛡️ 管理后台
          </button>
        </div>
        <div class="header-actions">
          <el-tag v-if="paymentStatus.paid" type="success" effect="plain" round>
            👑 {{ planLabel }}
          </el-tag>
          <el-tag v-else type="info" effect="plain" round class="vip-tag" @click="showPaymentDialog">
            开通会员
          </el-tag>
        </div>
      </div>
    </header>

    <!-- ============ 部署 Tab ============ -->
    <main v-if="activeTab === 'deploy'" class="main-content">
      <!-- Step 1 -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num">1</span>
          <span class="step-title">输入项目路径</span>
        </div>
        <div class="step-body">
          <el-input v-model="projectPath" placeholder="/path/to/your/project" size="large" clearable @keyup.enter="detectProject">
            <template #prefix><el-icon><Folder /></el-icon></template>
            <template #append>
              <el-button type="primary" :loading="detecting" @click="detectProject">
                <el-icon v-if="!detecting"><Search /></el-icon>
                检测
              </el-button>
            </template>
          </el-input>
        </div>
      </section>

      <!-- Step 2 -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">2</span>
          <span class="step-title">项目信息</span>
        </div>
        <div class="step-body">
          <div class="info-grid">
            <div class="info-item"><span class="info-label">📦 项目名称</span><span class="info-value highlight">{{ projectInfo.project_name }}</span></div>
            <div class="info-item"><span class="info-label">🏗️ 项目类型</span><el-tag :type="typeTagColor(projectInfo.type)" effect="dark">{{ projectInfo.type }}</el-tag></div>
            <div class="info-item"><span class="info-label">🔧 框架</span><el-tag v-if="projectInfo.framework" type="info" effect="plain">{{ projectInfo.framework }}</el-tag><span v-else class="info-value dim">-</span></div>
            <div class="info-item"><span class="info-label">📋 包管理器</span><el-tag v-if="projectInfo.package_manager" type="warning" effect="plain">{{ projectInfo.package_manager }}</el-tag><span v-else class="info-value dim">-</span></div>
            <div class="info-item"><span class="info-label">🐳 Docker</span><el-tag :type="projectInfo.has_docker ? 'success' : 'info'" effect="plain">{{ projectInfo.has_docker ? '已配置' : '未配置' }}</el-tag></div>
            <div class="info-item" v-if="projectInfo.entry_point"><span class="info-label">🔗 入口</span><span class="info-value code">{{ projectInfo.entry_point }}</span></div>
          </div>
        </div>
      </section>

      <!-- Step 3 -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">3</span>
          <span class="step-title">部署配置</span>
        </div>
        <div class="step-body">
          <div class="config-row">
            <div class="config-item">
              <label>部署方式</label>
              <el-select v-model="deployType" placeholder="选择部署方式" size="large" style="width:100%">
                <el-option v-for="opt in deployOptions" :key="opt.value" :label="opt.label" :value="opt.value">
                  <span>{{ opt.icon }} {{ opt.label }}</span>
                </el-option>
              </el-select>
            </div>
            <div class="config-item" v-if="deployType === 'server' && servers.length > 0">
              <label>目标服务器</label>
              <el-select v-model="selectedServerIdx" placeholder="选择服务器" size="large" style="width:100%">
                <el-option v-for="(s, i) in servers" :key="i" :label="`${s.name} (${s.host})`" :value="i" />
              </el-select>
            </div>
            <div class="config-item" v-if="deployType === 'server'">
              <label>域名/IP</label>
              <el-input v-model="domain" placeholder="example.com 或 IP" size="large" />
            </div>
          </div>
        </div>
      </section>

      <!-- Step 4 -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">4</span>
          <span class="step-title">生成部署脚本</span>
        </div>
        <div class="step-body">
          <div class="action-row">
            <el-button type="primary" size="large" :loading="generating" @click="generateScript">
              <el-icon v-if="!generating"><VideoPlay /></el-icon>
              生成脚本
            </el-button>
            <el-button v-if="scriptOutput && deployType === 'server'" type="success" size="large" :disabled="remoteDeploying" @click="startRemoteDeploy">
              <el-icon v-if="!remoteDeploying"><Upload /></el-icon>
              {{ remoteDeploying ? '部署中...' : '🚀 远程部署' }}
            </el-button>
          </div>

          <!-- Terminal Output -->
          <div v-if="scriptOutput" class="terminal-container fade-in">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">{{ scriptFilename }}</span>
              <div class="terminal-actions">
                <el-button text size="small" @click="copyScript"><el-icon><CopyDocument /></el-icon>{{ copied ? '已复制!' : '复制' }}</el-button>
                <el-button text size="small" @click="downloadScript"><el-icon><Download /></el-icon>下载</el-button>
              </div>
            </div>
            <div class="terminal-body"><pre><code>{{ scriptOutput }}</code></pre></div>
          </div>

          <!-- Remote Deploy Log -->
          <div v-if="remoteLogs.length > 0" class="terminal-container fade-in remote-log">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">🚀 远程部署日志</span>
              <div class="terminal-actions">
                <el-tag v-if="remoteStatus === 'success'" type="success" size="small">部署成功</el-tag>
                <el-tag v-else-if="remoteStatus === 'failed' || remoteStatus === 'error'" type="danger" size="small">部署失败</el-tag>
                <el-tag v-else type="warning" size="small" class="pulse-tag">部署中...</el-tag>
              </div>
            </div>
            <div class="terminal-body" ref="remoteLogBody">
              <pre><code v-for="(log, i) in remoteLogs" :key="i" :class="{'log-warn': log.startsWith('⚠️'), 'log-err': log.startsWith('❌'), 'log-ok': log.startsWith('✅') || log.startsWith('🎉')}">{{ log }}</code></pre>
            </div>
          </div>

          <!-- Extra files -->
          <div v-if="extraFiles.length > 0" class="extra-files fade-in">
            <h4>📎 附加文件</h4>
            <div v-for="file in extraFiles" :key="file.filename" class="extra-file-item">
              <div class="extra-file-header">
                <span>{{ file.filename }}</span>
                <el-button text size="small" @click="copyExtra(file.content)"><el-icon><CopyDocument /></el-icon></el-button>
                <el-button text size="small" @click="downloadExtra(file)"><el-icon><Download /></el-icon></el-button>
              </div>
              <div class="terminal-body compact"><pre><code>{{ file.content }}</code></pre></div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 生成项目 Tab ============ -->
    <main v-if="activeTab === 'generate'" class="main-content">
      <section class="step-section">
        <div class="step-header">
          <span class="step-num gen-num">1</span>
          <span class="step-title">描述你的项目</span>
        </div>
        <div class="step-body">
          <el-input v-model="genDescription" type="textarea" :rows="3" placeholder="描述你想要的项目，例如：一个带用户登录和任务管理的 Todo List 应用" size="large" />
          <div class="config-row" style="margin-top: 16px;">
            <div class="config-item">
              <label>项目类型</label>
              <el-select v-model="genProjectType" placeholder="选择类型" size="large" style="width:100%" @change="onGenTypeOnChange">
                <el-option value="frontend" label="🖥️ 前端项目" />
                <el-option value="backend" label="⚙️ 后端项目" />
                <el-option value="fullstack" label="🔗 全栈项目" />
              </el-select>
            </div>
            <div class="config-item">
              <label>技术栈</label>
              <el-select v-model="genTechStack" placeholder="选择技术栈" size="large" style="width:100%">
                <el-option v-for="(info, key) in currentStacks" :key="key" :value="key" :label="info.label">
                  <span>{{ info.label }}</span>
                  <span style="color: #8b949e; font-size: 12px; margin-left: 8px;">{{ info.desc }}</span>
                </el-option>
              </el-select>
            </div>
          </div>
        </div>
      </section>

      <section class="step-section fade-in">
        <div class="step-header">
          <span class="step-num gen-num">2</span>
          <span class="step-title">AI 生成代码</span>
        </div>
        <div class="step-body">
          <el-button type="primary" size="large" :loading="genLoading" @click="generateProject" :disabled="!genDescription.trim()">
            <el-icon v-if="!genLoading"><MagicStick /></el-icon>
            AI 生成项目
          </el-button>
          <span v-if="!paymentStatus.paid" class="pay-hint">
            <el-icon><Lock /></el-icon> 需要开通会员
          </span>
        </div>
      </section>

      <section v-if="genFiles.length > 0" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num gen-num">3</span>
          <span class="step-title">生成结果</span>
          <span class="selected-count">共 {{ genFiles.length }} 个文件</span>
        </div>
        <div class="step-body">
          <div class="gen-file-list">
            <div v-for="(file, idx) in genFiles" :key="idx" class="gen-file-item" :class="{ active: genSelectedFile === idx }" @click="genSelectedFile = idx">
              <span class="gen-file-icon">📄</span>
              <span class="gen-file-name">{{ file.filename }}</span>
            </div>
          </div>
          <div v-if="genSelectedFile >= 0 && genFiles[genSelectedFile]" class="terminal-container">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">{{ genFiles[genSelectedFile].filename }}</span>
              <div class="terminal-actions">
                <el-button text size="small" @click="copyGenFile"><el-icon><CopyDocument /></el-icon>复制</el-button>
              </div>
            </div>
            <div class="terminal-body"><pre><code>{{ genFiles[genSelectedFile].content }}</code></pre></div>
          </div>
          <div class="gen-actions" v-if="genFiles.length > 0">
            <el-button type="success" size="large" @click="downloadGenProject">
              <el-icon><Download /></el-icon>
              下载 ZIP
            </el-button>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 代码检测 Tab ============ -->
    <main v-if="activeTab === 'fix'" class="main-content">
      <section class="step-section">
        <div class="step-header">
          <span class="step-num fix-num">1</span>
          <span class="step-title">输入项目路径</span>
        </div>
        <div class="step-body">
          <el-input v-model="fixProjectPath" placeholder="/path/to/your/project" size="large" clearable @keyup.enter="analyzeCode">
            <template #prefix><el-icon><Folder /></el-icon></template>
            <template #append>
              <el-button type="warning" :loading="analyzing" @click="analyzeCode">
                <el-icon v-if="!analyzing"><Search /></el-icon>
                检测错误
              </el-button>
            </template>
          </el-input>
        </div>
      </section>

      <section v-if="analysisResult" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num fix-num">2</span>
          <span class="step-title">检测结果</span>
          <div class="result-summary" v-if="analysisResult.total > 0">
            <el-tag type="danger" effect="dark" size="small">{{ analysisResult.error_count }} 个错误</el-tag>
            <el-tag type="warning" effect="dark" size="small">{{ analysisResult.warning_count }} 个警告</el-tag>
          </div>
          <div class="result-summary" v-else>
            <el-tag type="success" effect="dark" size="small">✓ 未发现问题</el-tag>
          </div>
        </div>
        <div class="step-body">
          <div v-if="analysisResult.total === 0" class="no-errors">
            <span class="no-errors-icon">🎉</span>
            <p>恭喜！未检测到代码错误</p>
          </div>
          <div v-else class="error-list">
            <div v-for="(err, idx) in analysisResult.errors" :key="idx" class="error-item" :class="[err.severity, { selected: selectedErrors.includes(idx) }]" @click="toggleError(idx)">
              <div class="error-left">
                <span class="error-severity" :class="err.severity">{{ err.severity === 'error' ? '✕' : '⚠' }}</span>
                <span class="error-type-badge">{{ errorTypeLabel(err.error_type) }}</span>
              </div>
              <div class="error-center">
                <span class="error-file">{{ err.file }}</span>
                <span class="error-line" v-if="err.line > 0">:{{ err.line }}</span>
                <p class="error-msg">{{ err.error }}</p>
              </div>
              <div class="error-right">
                <el-checkbox :model-value="selectedErrors.includes(idx)" @click.stop="toggleError(idx)" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="selectedErrors.length > 0" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num fix-num">3</span>
          <span class="step-title">自动修复</span>
          <span class="selected-count">已选 {{ selectedErrors.length }} 项</span>
        </div>
        <div class="step-body">
          <div class="fix-actions">
            <el-button type="warning" size="large" :loading="repairing" @click="repairErrors">
              <el-icon v-if="!repairing"><Magic /></el-icon>
              AI 自动修复
            </el-button>
            <span v-if="!paymentStatus.paid" class="pay-hint">
              <el-icon><Lock /></el-icon> 需要开通会员
            </span>
            <el-button size="large" @click="selectAllErrors">全选</el-button>
            <el-button size="large" @click="selectedErrors = []">清空</el-button>
          </div>
          <div v-if="repairResults.length > 0" class="repair-results fade-in">
            <h4>📝 修复对比</h4>
            <div v-for="(result, ridx) in repairResults" :key="ridx" class="repair-item">
              <div class="repair-file-header">
                <span class="repair-filename">{{ result.file }}</span>
                <el-button type="success" size="small" :disabled="result.applied" @click="applyFix(result)">
                  {{ result.applied ? '✓ 已应用' : '应用修复' }}
                </el-button>
              </div>
              <div class="diff-container">
                <div class="diff-side">
                  <div class="diff-label">原始代码</div>
                  <pre class="diff-code original"><code>{{ result.original }}</code></pre>
                </div>
                <div class="diff-divider"></div>
                <div class="diff-side">
                  <div class="diff-label">修复后</div>
                  <pre class="diff-code fixed"><code>{{ result.fixed }}</code></pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 管理后台 Tab ============ -->
    <main v-if="activeTab === 'admin' && isAdmin" class="main-content">
      <!-- Admin Sub-tabs -->
      <div class="admin-subtabs">
        <button class="subtab-btn" :class="{ active: adminSubTab === 'dashboard' }" @click="adminSubTab = 'dashboard'; loadAdminStats()">📊 仪表盘</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'users' }" @click="adminSubTab = 'users'; loadAdminUsers()">👥 用户管理</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'orders' }" @click="adminSubTab = 'orders'; loadAdminOrders()">📋 订单管理</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'logs' }" @click="adminSubTab = 'logs'; loadDeployLogs()">📝 部署日志</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'config' }" @click="adminSubTab = 'config'">⚙️ 系统配置</button>
      </div>

      <!-- Dashboard -->
      <section v-if="adminSubTab === 'dashboard'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">📊</span>
          <span class="step-title">数据概览</span>
        </div>
        <div class="step-body">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-info">
                <div class="stat-value">{{ adminStats.total_users }}</div>
                <div class="stat-label">总用户数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">💎</div>
              <div class="stat-info">
                <div class="stat-value">{{ adminStats.paid_users }}</div>
                <div class="stat-label">付费用户</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📈</div>
              <div class="stat-info">
                <div class="stat-value">{{ paidRate }}%</div>
                <div class="stat-label">付费率</div>
              </div>
            </div>
            <div class="stat-card accent-orange">
              <div class="stat-icon">💰</div>
              <div class="stat-info">
                <div class="stat-value">¥{{ adminStats.monthly_income }}</div>
                <div class="stat-label">本月收入</div>
              </div>
            </div>
            <div class="stat-card accent-blue">
              <div class="stat-icon">💵</div>
              <div class="stat-info">
                <div class="stat-value">¥{{ adminStats.total_income }}</div>
                <div class="stat-label">总收入</div>
              </div>
            </div>
            <div class="stat-card accent-green">
              <div class="stat-icon">📦</div>
              <div class="stat-info">
                <div class="stat-value">{{ adminStats.total_orders }}</div>
                <div class="stat-label">总订单</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Users Management -->
      <section v-if="adminSubTab === 'users'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">👥</span>
          <span class="step-title">用户管理</span>
          <span class="selected-count">{{ adminUsers.length }} 位用户</span>
        </div>
        <div class="step-body">
          <el-input v-model="userSearchQuery" placeholder="搜索用户 ID..." size="default" clearable style="margin-bottom: 16px; max-width: 300px;">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户 ID</th>
                  <th>付费类型</th>
                  <th>付费时间</th>
                  <th>到期时间</th>
                  <th>注册时间</th>
                  <th>管理员</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.user_id">
                  <td class="user-id-cell">{{ user.user_id }}</td>
                  <td>
                    <el-tag :type="userPaidTypeTag(user.paid_type)" size="small" effect="dark">
                      {{ userPaidTypeLabel(user.paid_type) }}
                    </el-tag>
                  </td>
                  <td class="time-cell">{{ formatTime(user.paid_at) }}</td>
                  <td class="time-cell">{{ formatTime(user.expires_at) }}</td>
                  <td class="time-cell">{{ formatTime(user.created_at) }}</td>
                  <td>
                    <el-tag v-if="user.is_admin" type="danger" size="small" effect="dark">Admin</el-tag>
                    <span v-else class="dim">-</span>
                  </td>
                  <td>
                    <el-dropdown trigger="click" @command="(cmd) => handleUserAction(user, cmd)">
                      <el-button size="small" type="primary" text>操作</el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="free">设为免费</el-dropdown-item>
                          <el-dropdown-item command="monthly">设为月付</el-dropdown-item>
                          <el-dropdown-item command="yearly">设为年付</el-dropdown-item>
                          <el-dropdown-item command="permanent">设为永久</el-dropdown-item>
                          <el-dropdown-item divided :command="user.is_admin ? 'revoke_admin' : 'grant_admin'">
                            {{ user.is_admin ? '取消管理员' : '设为管理员' }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Orders Management -->
      <section v-if="adminSubTab === 'orders'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">📋</span>
          <span class="step-title">订单管理</span>
          <span class="selected-count">{{ adminOrders.length }} 笔订单</span>
        </div>
        <div class="step-body">
          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>订单 ID</th>
                  <th>用户</th>
                  <th>金额</th>
                  <th>套餐</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>支付时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="order in adminOrders" :key="order.order_id">
                  <td class="user-id-cell">{{ order.order_id }}</td>
                  <td class="user-id-cell">{{ order.user_id }}</td>
                  <td class="amount-cell">¥{{ order.amount }}</td>
                  <td>{{ planTypeLabel(order.paid_type) }}</td>
                  <td>
                    <el-tag :type="order.status === 'paid' ? 'success' : 'warning'" size="small" effect="dark">
                      {{ order.status === 'paid' ? '已支付' : '待支付' }}
                    </el-tag>
                  </td>
                  <td class="time-cell">{{ formatTime(order.created_at) }}</td>
                  <td class="time-cell">{{ formatTime(order.paid_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Deploy Logs -->
      <section v-if="adminSubTab === 'logs'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">📝</span>
          <span class="step-title">部署日志</span>
        </div>
        <div class="step-body">
          <div v-if="deployLogs.length === 0" class="empty-state">
            <span>📝</span>
            <p>暂无部署日志</p>
          </div>
          <div v-else class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户</th>
                  <th>项目</th>
                  <th>部署方式</th>
                  <th>状态</th>
                  <th>信息</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in deployLogs" :key="log.id">
                  <td class="user-id-cell">{{ log.user_id }}</td>
                  <td>{{ log.project_name }}</td>
                  <td>{{ log.deploy_type }}</td>
                  <td>
                    <el-tag :type="logStatusTag(log.status)" size="small" effect="dark">{{ log.status }}</el-tag>
                  </td>
                  <td class="msg-cell">{{ log.message }}</td>
                  <td class="time-cell">{{ formatTime(log.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- System Config -->
      <section v-if="adminSubTab === 'config'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">⚙️</span>
          <span class="step-title">系统配置</span>
        </div>
        <div class="step-body">
          <div class="config-section">
            <h4>🏷️ 价格配置</h4>
            <div class="config-form">
              <div class="config-form-item">
                <label>月度会员价格 (¥)</label>
                <el-input v-model.number="configPrices.monthly" type="number" size="default" style="width: 120px;" />
              </div>
              <div class="config-form-item">
                <label>年度会员价格 (¥)</label>
                <el-input v-model.number="configPrices.yearly" type="number" size="default" style="width: 120px;" />
              </div>
            </div>
            <p class="config-hint">⚠️ 当前价格配置为前端展示，修改后需重新部署生效</p>
          </div>
          <div class="config-section">
            <h4>🔑 管理员 Token</h4>
            <div class="config-form">
              <div class="config-form-item">
                <label>当前 Token</label>
                <el-input v-model="adminToken" type="password" show-password size="default" style="width: 300px;" placeholder="设置管理员 Token" />
              </div>
            </div>
            <p class="config-hint">通过请求头 <code>X-Admin-Token</code> 验证管理员身份</p>
          </div>
          <div class="config-section">
            <h4>📊 数据库信息</h4>
            <div class="info-grid" style="margin-top: 12px;">
              <div class="info-item"><span class="info-label">用户总数</span><span class="info-value">{{ adminStats.total_users }}</span></div>
              <div class="info-item"><span class="info-label">付费用户</span><span class="info-value">{{ adminStats.paid_users }}</span></div>
              <div class="info-item"><span class="info-label">总订单数</span><span class="info-value">{{ adminStats.total_orders }}</span></div>
              <div class="info-item"><span class="info-label">已支付订单</span><span class="info-value">{{ adminStats.paid_orders }}</span></div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 付费弹窗 ============ -->
    <el-dialog v-model="paymentDialogVisible" title="开通会员" width="520px" :close-on-click-modal="false" class="payment-dialog">
      <div class="payment-content">
        <div class="payment-plans">
          <div v-for="plan in planOptions" :key="plan.key" class="plan-card" :class="{ selected: selectedPlan === plan.key, recommend: plan.recommend }" @click="selectedPlan = plan.key">
            <div v-if="plan.recommend" class="plan-badge">推荐</div>
            <div class="plan-name">{{ plan.label }}</div>
            <div class="plan-price">
              <span class="price-symbol">¥</span>
              <span class="price-num">{{ plan.price }}</span>
            </div>
            <div class="plan-desc">{{ plan.desc }}</div>
            <div class="plan-unit">{{ plan.unit }}</div>
          </div>
        </div>
        <div class="payment-features">
          <div class="feature-item" v-for="feat in paymentFeatures" :key="feat">
            <span class="feat-check">✓</span> {{ feat }}
          </div>
        </div>
      </div>
      <template #footer>
        <div class="payment-footer">
          <el-button v-if="paymentStatus.paid" type="success" disabled>
            已是会员 · {{ planLabel }}
          </el-button>
          <el-button v-else type="primary" size="large" :loading="payLoading" @click="handlePay" style="width: 200px;">
            立即开通
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Admin Login Dialog -->
    <el-dialog v-model="adminLoginVisible" title="管理员验证" width="400px" :close-on-click-modal="false">
      <div class="admin-login-content">
        <p style="margin-bottom: 16px; color: var(--text-secondary); font-size: 14px;">请输入管理员 Token 以访问管理后台</p>
        <el-input v-model="adminTokenInput" type="password" show-password placeholder="输入管理员 Token" size="large" @keyup.enter="verifyAdminToken" />
      </div>
      <template #footer>
        <el-button @click="adminLoginVisible = false">取消</el-button>
        <el-button type="primary" @click="verifyAdminToken">验证</el-button>
      </template>
    </el-dialog>

    <!-- Edit User Dialog -->
    <el-dialog v-model="editUserDialogVisible" title="修改用户付费状态" width="420px">
      <div v-if="editingUser" style="margin-bottom: 16px;">
        <p style="color: var(--text-secondary); font-size: 14px;">用户: <code>{{ editingUser.user_id }}</code></p>
      </div>
      <el-form label-width="80px">
        <el-form-item label="付费类型">
          <el-select v-model="editUserForm.paid_type" style="width: 100%;">
            <el-option value="free" label="免费用户" />
            <el-option value="monthly" label="月度会员" />
            <el-option value="yearly" label="年度会员" />
            <el-option value="permanent" label="永久会员" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期时间" v-if="editUserForm.paid_type !== 'free' && editUserForm.paid_type !== 'permanent'">
          <el-date-picker v-model="editUserForm.expires_at" type="datetime" placeholder="选择到期时间" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editUserDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editUserLoading" @click="confirmEditUser">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- Footer -->
    <footer class="app-footer">
      <span>AI Auto Deploy</span>
      <span class="separator">·</span>
      <span>智能识别 · 一键部署 · 代码检测 · 自动修复 · AI 生成</span>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      activeTab: 'deploy',
      // User & Payment
      userId: 'user_' + Math.random().toString(36).slice(2, 10),
      paymentStatus: { paid: false, paid_type: 'free' },
      paymentDialogVisible: false,
      payLoading: false,
      selectedPlan: 'yearly',
      planOptions: [
        { key: 'monthly', label: '月度会员', price: 99, desc: '适合短期项目', unit: '¥3.3/天', recommend: false },
        { key: 'yearly', label: '年度会员', price: 666, desc: '省 522 元，超值', unit: '¥1.8/天', recommend: true },
      ],
      paymentFeatures: [
        'AI 生成完整项目代码',
        'AI 自动修复代码错误',
        '无限次使用',
        '远程部署到服务器',
        '优先技术支持',
      ],
      // Deploy tab
      projectPath: '',
      projectInfo: null,
      detecting: false,
      generating: false,
      deployType: 'local',
      selectedServerIdx: 0,
      domain: '',
      servers: [],
      scriptOutput: '',
      scriptFilename: '',
      extraFiles: [],
      copied: false,
      deployOptions: [
        { value: 'local', label: '本地脚本', icon: '📝' },
        { value: 'server', label: '云服务器 (SSH)', icon: '🖥️' },
        { value: 'cloudflare', label: 'Cloudflare Pages', icon: '☁️' },
        { value: 'docker', label: 'Docker', icon: '🐳' },
      ],
      // Remote deploy
      remoteDeploying: false,
      remoteLogs: [],
      remoteStatus: '',
      // Generate tab
      genDescription: '',
      genProjectType: 'frontend',
      genTechStack: 'vue3',
      genLoading: false,
      genFiles: [],
      genSelectedFile: -1,
      techStacks: {
        frontend: {
          vue3: { label: 'Vue 3 + Vite', desc: 'Vue 3 组合式 API + Vite 构建工具' },
          react: { label: 'React 18', desc: 'React 18 + Hooks + Vite' },
          html: { label: '原生 HTML/CSS/JS', desc: '纯前端，无框架依赖' },
        },
        backend: {
          fastapi: { label: 'FastAPI', desc: 'Python 异步框架' },
          flask: { label: 'Flask', desc: 'Python 轻量级框架' },
          express: { label: 'Express.js', desc: 'Node.js 框架' },
        },
        fullstack: {
          nextjs: { label: 'Next.js', desc: 'React 全栈框架' },
          nuxtjs: { label: 'Nuxt.js', desc: 'Vue 全栈框架' },
        },
      },
      // Fix tab
      fixProjectPath: '',
      analyzing: false,
      analysisResult: null,
      selectedErrors: [],
      repairing: false,
      repairResults: [],
      // Admin
      isAdmin: false,
      adminSubTab: 'dashboard',
      logoClickCount: 0,
      adminLoginVisible: false,
      adminTokenInput: '',
      adminToken: '',
      adminStats: { total_users: 0, paid_users: 0, free_users: 0, monthly_income: 0, total_income: 0, total_orders: 0, paid_orders: 0 },
      adminUsers: [],
      adminOrders: [],
      deployLogs: [],
      userSearchQuery: '',
      editUserDialogVisible: false,
      editUserLoading: false,
      editingUser: null,
      editUserForm: { paid_type: 'free', expires_at: null },
      configPrices: { monthly: 99, yearly: 666 },
    }
  },
  computed: {
    currentStacks() {
      return this.techStacks[this.genProjectType] || {}
    },
    planLabel() {
      const map = { monthly: '月度会员', yearly: '年度会员', permanent: '永久会员' }
      return map[this.paymentStatus.paid_type] || '会员'
    },
    paidRate() {
      if (this.adminStats.total_users === 0) return 0
      return ((this.adminStats.paid_users / this.adminStats.total_users) * 100).toFixed(1)
    },
    filteredUsers() {
      if (!this.userSearchQuery) return this.adminUsers
      const q = this.userSearchQuery.toLowerCase()
      return this.adminUsers.filter(u => u.user_id.toLowerCase().includes(q))
    },
  },
  watch: {
    logoClickCount(val) {
      if (val >= 5 && !this.isAdmin) {
        this.logoClickCount = 0
        this.adminLoginVisible = true
      }
    },
  },
  mounted() {
    // Check for admin URL param
    const urlParams = new URLSearchParams(window.location.search)
    const adminParam = urlParams.get('admin')
    if (adminParam === '1') {
      this.adminLoginVisible = true
    }

    this.loadServers()
    this.checkPaymentStatus()
    this.checkAdminStatus()
  },
  methods: {
    // ===== Admin =====
    async checkAdminStatus() {
      try {
        const res = await axios.get('/api/admin/verify', {
          headers: { 'x-user-id': this.userId },
        })
        this.isAdmin = res.data.is_admin
      } catch {
        this.isAdmin = false
      }
    },
    async verifyAdminToken() {
      try {
        const res = await axios.get('/api/admin/verify', {
          headers: {
            'x-admin-token': this.adminTokenInput,
            'x-user-id': this.userId,
          },
        })
        if (res.data.is_admin) {
          this.isAdmin = true
          this.adminToken = this.adminTokenInput
          this.adminLoginVisible = false
          this.$message.success('管理员验证成功')
          this.loadAdminStats()
        } else {
          this.$message.error('Token 无效')
        }
      } catch {
        this.$message.error('验证失败')
      }
    },
    getAdminHeaders() {
      const headers = { 'x-user-id': this.userId }
      if (this.adminToken) {
        headers['x-admin-token'] = this.adminToken
      }
      return headers
    },
    async loadAdminStats() {
      try {
        const res = await axios.get('/api/admin/stats', { headers: this.getAdminHeaders() })
        this.adminStats = res.data
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async loadAdminUsers() {
      try {
        const res = await axios.get('/api/admin/users', { headers: this.getAdminHeaders() })
        this.adminUsers = res.data.users || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async loadAdminOrders() {
      try {
        const res = await axios.get('/api/admin/orders', { headers: this.getAdminHeaders() })
        this.adminOrders = res.data.orders || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async loadDeployLogs() {
      try {
        const res = await axios.get('/api/admin/logs', { headers: this.getAdminHeaders() })
        this.deployLogs = res.data.logs || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async handleUserAction(user, command) {
      if (command === 'grant_admin' || command === 'revoke_admin') {
        try {
          await axios.post('/api/admin/set-admin', {
            user_id: user.user_id,
            is_admin: command === 'grant_admin',
          }, { headers: this.getAdminHeaders() })
          this.$message.success(command === 'grant_admin' ? '已设为管理员' : '已取消管理员')
          await this.loadAdminUsers()
        } catch (err) {
          this.$message.error(err.response?.data?.detail || '操作失败')
        }
        return
      }
      // Open edit dialog for paid type changes
      this.editingUser = user
      this.editUserForm.paid_type = command || user.paid_type
      this.editUserForm.expires_at = null
      if (command && command !== 'free') {
        // Set default expiry based on plan type
        const now = new Date()
        if (command === 'monthly') now.setDate(now.getDate() + 30)
        else if (command === 'yearly') now.setDate(now.getDate() + 365)
        this.editUserForm.expires_at = now
      }

      // Quick update for simple commands
      if (command && ['free', 'monthly', 'yearly', 'permanent'].includes(command)) {
        this.editUserDialogVisible = true
      }
    },
    async confirmEditUser() {
      this.editUserLoading = true
      try {
        const expiresAt = this.editUserForm.expires_at
          ? new Date(this.editUserForm.expires_at).toISOString()
          : null

        await axios.put(`/api/admin/users/${this.editingUser.user_id}`, {
          paid_type: this.editUserForm.paid_type,
          expires_at: expiresAt,
        }, { headers: this.getAdminHeaders() })

        this.$message.success('用户状态已更新')
        this.editUserDialogVisible = false
        await this.loadAdminUsers()
        await this.loadAdminStats()
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '更新失败')
      } finally {
        this.editUserLoading = false
      }
    },
    userPaidTypeTag(type) {
      return { free: 'info', monthly: '', yearly: 'warning', permanent: 'danger' }[type] || 'info'
    },
    userPaidTypeLabel(type) {
      return { free: '免费', monthly: '月付', yearly: '年付', permanent: '永久' }[type] || type
    },
    planTypeLabel(type) {
      return { monthly: '月度会员', yearly: '年度会员', permanent: '永久会员' }[type] || type || '-'
    },
    formatTime(t) {
      if (!t) return '-'
      try {
        return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      } catch { return t }
    },
    logStatusTag(status) {
      return { success: 'success', failed: 'danger', error: 'danger', running: 'warning' }[status] || 'info'
    },
    // ===== Payment =====
    async checkPaymentStatus() {
      try {
        const res = await axios.get(`/api/payment/user/${this.userId}`)
        this.paymentStatus = {
          paid: res.data.paid,
          paid_type: res.data.paid_type || 'free',
          expires_at: res.data.expires_at,
        }
      } catch { /* ignore */ }
    },
    showPaymentDialog() {
      this.paymentDialogVisible = true
    },
    async handlePay() {
      this.payLoading = true
      try {
        const res = await axios.post('/api/payment/create', {
          user_id: this.userId,
          plan: this.selectedPlan,
        })
        if (res.data.already_paid) {
          this.$message.success('您已是会员')
          this.paymentDialogVisible = false
          await this.checkPaymentStatus()
          return
        }
        if (res.data.pay_url) {
          window.open(res.data.pay_url, '_blank')
          this.$message.info('请在新窗口完成支付')
          this.pollPaymentStatus(res.data.order_id)
        }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '创建支付失败')
      } finally {
        this.payLoading = false
      }
    },
    async pollPaymentStatus(orderId) {
      const maxRetries = 30
      for (let i = 0; i < maxRetries; i++) {
        await new Promise(r => setTimeout(r, 3000))
        try {
          const res = await axios.get(`/api/payment/check/${orderId}`)
          if (res.data.status === 'paid') {
            this.$message.success('支付成功！已开通会员')
            this.paymentDialogVisible = false
            await this.checkPaymentStatus()
            return
          }
        } catch { /* continue */ }
      }
      this.$message.info('支付确认中，请稍后刷新页面查看')
    },
    async requirePayment(feature) {
      if (this.paymentStatus.paid) return true
      this.showPaymentDialog()
      return false
    },
    // ===== Deploy =====
    async detectProject() {
      if (!this.projectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      this.detecting = true
      this.projectInfo = null
      this.scriptOutput = ''
      try {
        const res = await axios.post('/api/deploy/detect', { path: this.projectPath })
        this.projectInfo = res.data
        this.domain = res.data.project_name
        this.$message.success('项目检测完成')
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '检测失败')
      } finally { this.detecting = false }
    },
    async generateScript() {
      this.generating = true
      this.scriptOutput = ''
      this.extraFiles = []
      this.remoteLogs = []
      this.remoteStatus = ''
      try {
        const payload = { path: this.projectPath, deploy_type: this.deployType, domain: this.domain || undefined }
        if (this.deployType === 'server' && this.servers.length > 0) {
          payload.server = this.servers[this.selectedServerIdx]
        }
        const res = await axios.post('/api/deploy/generate', payload)
        this.scriptOutput = res.data.script
        this.scriptFilename = res.data.filename
        this.extraFiles = res.data.extra_files || []
        this.$message.success('脚本生成成功')
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '生成失败')
      } finally { this.generating = false }
    },
    async loadServers() {
      try {
        const res = await axios.get('/api/servers')
        this.servers = res.data.servers || []
      } catch { this.servers = [] }
    },
    async startRemoteDeploy() {
      if (!(await this.requirePayment('deploy'))) return
      if (!this.scriptOutput) { this.$message.warning('请先生成部署脚本'); return }

      this.remoteDeploying = true
      this.remoteLogs = []
      this.remoteStatus = 'connecting'

      try {
        const resp = await fetch('/api/deploy/remote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            server_index: this.selectedServerIdx,
            script: this.scriptOutput,
            project_path: this.projectPath,
          }),
        })

        const reader = resp.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              this.remoteLogs.push(line.slice(6))
              this.$nextTick(() => {
                const el = this.$refs.remoteLogBody
                if (el) el.scrollTop = el.scrollHeight
              })
            } else if (line.startsWith('event: done')) {
              this.remoteDeploying = false
            }
          }
        }

        const lastLog = this.remoteLogs[this.remoteLogs.length - 1] || ''
        if (lastLog.includes('🎉') || lastLog.includes('部署完成')) {
          this.remoteStatus = 'success'
        } else {
          this.remoteStatus = 'failed'
        }
      } catch (err) {
        this.remoteLogs.push(`❌ 连接错误: ${err.message}`)
        this.remoteStatus = 'error'
      } finally {
        this.remoteDeploying = false
      }
    },
    copyScript() {
      navigator.clipboard.writeText(this.scriptOutput)
      this.copied = true
      setTimeout(() => { this.copied = false }, 2000)
    },
    copyExtra(content) { navigator.clipboard.writeText(content); this.$message.success('已复制') },
    downloadScript() { this.downloadFile(this.scriptFilename, this.scriptOutput) },
    downloadExtra(file) { this.downloadFile(file.filename, file.content) },
    downloadFile(filename, content) {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
      URL.revokeObjectURL(url)
    },
    typeTagColor(type) { return { python: 'success', nodejs: 'warning', static: 'info' }[type] || '' },

    // ===== Generate =====
    onGenTypeOnChange() {
      const stacks = Object.keys(this.techStacks[this.genProjectType] || {})
      this.genTechStack = stacks[0] || ''
    },
    async generateProject() {
      if (!(await this.requirePayment('generate'))) return
      if (!this.genDescription.trim()) { this.$message.warning('请输入项目描述'); return }

      this.genLoading = true
      this.genFiles = []
      this.genSelectedFile = -1
      try {
        const res = await axios.post('/api/generate/project', {
          description: this.genDescription,
          project_type: this.genProjectType,
          tech_stack: this.genTechStack,
          user_id: this.userId,
        })
        this.genFiles = res.data.files || []
        if (this.genFiles.length > 0) this.genSelectedFile = 0
        this.$message.success(`项目生成完成，共 ${this.genFiles.length} 个文件`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '生成失败')
        }
      } finally { this.genLoading = false }
    },
    copyGenFile() {
      if (this.genSelectedFile >= 0 && this.genFiles[this.genSelectedFile]) {
        navigator.clipboard.writeText(this.genFiles[this.genSelectedFile].content)
        this.$message.success('已复制')
      }
    },
    async downloadGenProject() {
      try {
        const res = await axios.post('/api/generate/download', {
          files: this.genFiles,
          project_name: 'generated-project',
        }, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a'); a.href = url; a.download = 'generated-project.zip'; a.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        this.$message.error('下载失败')
      }
    },

    // ===== Code Fix =====
    async analyzeCode() {
      if (!this.fixProjectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      try {
        const res = await axios.post('/api/fix/analyze', { path: this.fixProjectPath })
        this.analysisResult = res.data
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '分析失败')
      } finally { this.analyzing = false }
    },
    toggleError(idx) {
      const pos = this.selectedErrors.indexOf(idx)
      if (pos === -1) this.selectedErrors.push(idx)
      else this.selectedErrors.splice(pos, 1)
    },
    selectAllErrors() {
      if (!this.analysisResult) return
      this.selectedErrors = this.analysisResult.errors.map((_, i) => i)
    },
    async repairErrors() {
      if (this.selectedErrors.length === 0) return
      if (!(await this.requirePayment('fix'))) return
      this.repairing = true
      this.repairResults = []
      try {
        const errors = this.selectedErrors.map(idx => this.analysisResult.errors[idx])
        const res = await axios.post('/api/fix/repair', { path: this.fixProjectPath, errors })
        this.repairResults = res.data.results.map(r => ({ ...r, applied: false }))
        this.$message.success(`AI 修复完成，共 ${this.repairResults.length} 个文件`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '修复失败')
        }
      } finally { this.repairing = false }
    },
    async applyFix(result) {
      try {
        await axios.post('/api/fix/apply', { path: this.fixProjectPath, fixes: [{ file: result.file, fixed: result.fixed }] })
        result.applied = true
        this.$message.success(`${result.file} 修复已应用`)
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '应用修复失败')
      }
    },
    errorTypeLabel(type) {
      return { syntax: '语法', import: '依赖', type: '类型', config: '配置', bracket: '括号' }[type] || type
    },
  },
}
</script>

<style scoped>
.app-container { min-height: 100vh; display: flex; flex-direction: column; max-width: 960px; margin: 0 auto; padding: 0 24px; }

/* Header */
.app-header { display: flex; align-items: center; justify-content: space-between; padding: 24px 0; border-bottom: 1px solid var(--border-color); }
.header-left { display: flex; align-items: center; gap: 12px; cursor: default; user-select: none; }
.header-right { display: flex; align-items: center; gap: 16px; }
.logo { font-size: 28px; }
.header-left h1 { font-size: 22px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
.version { font-size: 12px; color: var(--text-secondary); background: var(--bg-tertiary); padding: 2px 8px; border-radius: 10px; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.vip-tag { cursor: pointer; transition: all 0.2s; }
.vip-tag:hover { transform: scale(1.05); }

/* Tab Bar */
.tab-bar { display: flex; gap: 4px; background: var(--bg-tertiary); border-radius: 8px; padding: 3px; }
.tab-btn { padding: 6px 16px; border: none; border-radius: 6px; background: transparent; color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; font-family: inherit; white-space: nowrap; }
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { background: var(--bg-secondary); color: var(--text-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.admin-tab { color: var(--accent-orange); }
.admin-tab.active { background: rgba(210, 153, 34, 0.15); color: var(--accent-orange); }

/* Main */
.main-content { flex: 1; padding: 24px 0; display: flex; flex-direction: column; gap: 20px; }

/* Step Section */
.step-section { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
.step-header { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-bottom: 1px solid var(--border-color); background: var(--bg-tertiary); flex-wrap: wrap; }
.step-num { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: var(--accent-green); color: #000; font-weight: 700; font-size: 13px; border-radius: 50%; }
.step-num.fix-num { background: var(--accent-orange); }
.step-num.gen-num { background: var(--accent-purple); color: #fff; }
.step-num.admin-num { background: var(--accent-orange); color: #fff; font-size: 16px; width: auto; border-radius: 6px; padding: 0 6px; }
.step-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.step-body { padding: 20px; }
.result-summary { display: flex; gap: 8px; margin-left: auto; }
.selected-count { font-size: 13px; color: var(--accent-purple); margin-left: auto; }

/* Action Row */
.action-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }

/* Info Grid */
.info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.info-item { display: flex; flex-direction: column; gap: 6px; }
.info-label { font-size: 12px; color: var(--text-secondary); }
.info-value { font-size: 14px; font-weight: 500; }
.info-value.highlight { color: var(--accent-blue); }
.info-value.code { font-family: monospace; color: var(--accent-green); }
.info-value.dim { color: var(--text-secondary); }

/* Config Row */
.config-row { display: flex; gap: 16px; flex-wrap: wrap; }
.config-item { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 8px; }
.config-item label { font-size: 13px; color: var(--text-secondary); font-weight: 500; }

/* Terminal */
.terminal-container { margin-top: 20px; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.terminal-header { display: flex; align-items: center; padding: 10px 16px; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); gap: 12px; }
.terminal-dots { display: flex; gap: 6px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.red { background: #ff5f57; } .dot.yellow { background: #febc2e; } .dot.green { background: #28c840; }
.terminal-title { flex: 1; font-size: 13px; color: var(--text-secondary); text-align: center; }
.terminal-actions { display: flex; gap: 4px; }
.terminal-body { background: var(--terminal-bg); padding: 16px; max-height: 500px; overflow: auto; }
.terminal-body.compact { max-height: 300px; }
.terminal-body pre { margin: 0; white-space: pre-wrap; word-break: break-all; font-size: 13px; line-height: 1.6; color: var(--terminal-green); font-family: 'JetBrains Mono', 'Fira Code', monospace; }

/* Remote Log */
.remote-log .terminal-body pre code { display: block; padding: 2px 0; }
.log-warn { color: var(--accent-orange) !important; }
.log-err { color: #f85149 !important; }
.log-ok { color: var(--accent-green) !important; }
.pulse-tag { animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Extra files */
.extra-files { margin-top: 16px; }
.extra-files h4 { font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }
.extra-file-item { border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-bottom: 12px; }
.extra-file-header { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: var(--bg-tertiary); font-size: 13px; color: var(--text-primary); }

/* ===== Generate Tab ===== */
.pay-hint { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: var(--accent-orange); margin-left: 12px; cursor: pointer; }
.pay-hint:hover { text-decoration: underline; }

.gen-file-list { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; max-height: 200px; overflow-y: auto; }
.gen-file-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.gen-file-item:hover { background: var(--bg-tertiary); }
.gen-file-item.active { background: var(--bg-tertiary); border-color: var(--accent-purple); }
.gen-file-icon { font-size: 14px; }
.gen-file-name { font-size: 13px; color: var(--accent-blue); font-family: monospace; }
.gen-actions { margin-top: 16px; }

/* ===== Error List ===== */
.no-errors { text-align: center; padding: 32px 0; }
.no-errors-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.no-errors p { color: var(--text-secondary); font-size: 14px; }
.error-list { display: flex; flex-direction: column; gap: 8px; }
.error-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.error-item:hover { border-color: var(--text-secondary); }
.error-item.selected { border-color: var(--accent-orange); background: rgba(210, 153, 34, 0.05); }
.error-item.error { border-left: 3px solid #f85149; }
.error-item.warning { border-left: 3px solid #d29922; }
.error-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.error-severity { font-size: 16px; width: 24px; text-align: center; }
.error-severity.error { color: #f85149; } .error-severity.warning { color: #d29922; }
.error-type-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: var(--bg-tertiary); color: var(--text-secondary); white-space: nowrap; }
.error-center { flex: 1; min-width: 0; }
.error-file { font-size: 13px; color: var(--accent-blue); font-family: monospace; }
.error-line { font-size: 13px; color: var(--text-secondary); font-family: monospace; }
.error-msg { font-size: 12px; color: var(--text-secondary); margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.error-right { flex-shrink: 0; }

/* Fix Actions */
.fix-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; align-items: center; }

/* Repair Results / Diff */
.repair-results { margin-top: 12px; }
.repair-results h4 { font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }
.repair-item { border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-bottom: 16px; }
.repair-file-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); }
.repair-filename { font-size: 13px; color: var(--accent-blue); font-family: monospace; }
.diff-container { display: flex; background: var(--terminal-bg); overflow: hidden; }
.diff-side { flex: 1; min-width: 0; overflow: auto; max-height: 400px; }
.diff-label { padding: 6px 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); position: sticky; top: 0; z-index: 1; }
.diff-side:first-child .diff-label { color: #f85149; background: rgba(248, 81, 73, 0.08); }
.diff-side:last-child .diff-label { color: #3fb950; background: rgba(63, 185, 80, 0.08); }
.diff-code { margin: 0; padding: 12px; font-size: 12px; line-height: 1.6; font-family: 'JetBrains Mono', 'Fira Code', monospace; white-space: pre; color: var(--text-primary); }
.diff-divider { width: 1px; background: var(--border-color); flex-shrink: 0; }

/* ===== Payment Dialog ===== */
.payment-content { padding: 0 4px; }
.payment-plans { display: flex; gap: 16px; margin-bottom: 24px; }
.plan-card { flex: 1; border: 2px solid var(--border-color); border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.3s; position: relative; }
.plan-card:hover { border-color: var(--text-secondary); }
.plan-card.selected { border-color: var(--accent-blue); background: rgba(88, 166, 255, 0.05); }
.plan-card.recommend { border-color: var(--accent-blue); }
.plan-badge { position: absolute; top: -1px; right: 16px; background: var(--accent-blue); color: #fff; font-size: 11px; padding: 2px 10px; border-radius: 0 0 8px 8px; font-weight: 600; }
.plan-name { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; }
.plan-price { margin-bottom: 8px; }
.price-symbol { font-size: 16px; color: var(--accent-orange); font-weight: 600; }
.price-num { font-size: 36px; font-weight: 700; color: var(--accent-orange); }
.plan-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.plan-unit { font-size: 12px; color: var(--text-secondary); }
.payment-features { padding: 16px; background: var(--bg-tertiary); border-radius: 8px; }
.feature-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 14px; color: var(--text-primary); }
.feat-check { color: var(--accent-green); font-weight: 700; }
.payment-footer { text-align: center; }

/* ===== Admin Styles ===== */
.admin-subtabs { display: flex; gap: 4px; background: var(--bg-tertiary); border-radius: 8px; padding: 3px; flex-wrap: wrap; }
.subtab-btn { padding: 8px 16px; border: none; border-radius: 6px; background: transparent; color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.subtab-btn:hover { color: var(--text-primary); }
.subtab-btn.active { background: rgba(210, 153, 34, 0.15); color: var(--accent-orange); box-shadow: 0 1px 3px rgba(0,0,0,0.2); }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; background: var(--bg-tertiary); border-radius: 12px; border: 1px solid var(--border-color); transition: transform 0.2s; }
.stat-card:hover { transform: translateY(-2px); }
.stat-card.accent-orange { border-color: var(--accent-orange); }
.stat-card.accent-blue { border-color: var(--accent-blue); }
.stat-card.accent-green { border-color: var(--accent-green); }
.stat-icon { font-size: 32px; }
.stat-info { flex: 1; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

/* Admin Table */
.admin-table-wrapper { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { text-align: left; padding: 10px 12px; background: var(--bg-tertiary); color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-color); color: var(--text-primary); }
.admin-table tr:hover td { background: rgba(255,255,255,0.02); }
.user-id-cell { font-family: monospace; font-size: 12px; color: var(--accent-blue); max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.time-cell { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.amount-cell { font-weight: 600; color: var(--accent-orange); }
.msg-cell { font-size: 12px; color: var(--text-secondary); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dim { color: var(--text-secondary); }

/* Config Section */
.config-section { margin-bottom: 24px; }
.config-section h4 { font-size: 15px; color: var(--text-primary); margin-bottom: 12px; font-weight: 600; }
.config-form { display: flex; gap: 24px; flex-wrap: wrap; }
.config-form-item { display: flex; flex-direction: column; gap: 6px; }
.config-form-item label { font-size: 13px; color: var(--text-secondary); }
.config-hint { font-size: 12px; color: var(--text-secondary); margin-top: 8px; }
.config-hint code { background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-size: 11px; }

.empty-state { text-align: center; padding: 40px 0; color: var(--text-secondary); }
.empty-state span { font-size: 48px; display: block; margin-bottom: 12px; }

.admin-login-content { padding: 8px 0; }

/* Footer */
.app-footer { padding: 20px 0; text-align: center; font-size: 12px; color: var(--text-secondary); border-top: 1px solid var(--border-color); }
.separator { margin: 0 8px; }

/* Animations */
.fade-in { animation: fadeIn 0.3s ease-in; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* Responsive */
@media (max-width: 600px) {
  .app-container { padding: 0 12px; }
  .info-grid { grid-template-columns: 1fr; }
  .config-row { flex-direction: column; }
  .diff-container { flex-direction: column; }
  .diff-divider { width: auto; height: 1px; }
  .header-right { flex-direction: column; align-items: flex-end; gap: 8px; }
  .payment-plans { flex-direction: column; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
