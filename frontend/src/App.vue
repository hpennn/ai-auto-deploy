<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <span class="logo">🚀</span>
        <h1>AI Auto Deploy</h1>
        <span class="version">v1.1</span>
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
              <el-select v-model="genProjectType" placeholder="选择类型" size="large" style="width:100%" @change="onGenTypeChange">
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
  },
  mounted() {
    this.loadServers()
    this.checkPaymentStatus()
  },
  methods: {
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
          // Start polling payment status
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
            } else if (line.startsWith('event: status')) {
              // next data line is the status
            } else if (line.startsWith('event: done')) {
              this.remoteDeploying = false
            }
          }
        }

        // Determine final status
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
    onGenTypeChange() {
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
.header-left { display: flex; align-items: center; gap: 12px; }
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

/* Main */
.main-content { flex: 1; padding: 24px 0; display: flex; flex-direction: column; gap: 20px; }

/* Step Section */
.step-section { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
.step-header { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-bottom: 1px solid var(--border-color); background: var(--bg-tertiary); flex-wrap: wrap; }
.step-num { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: var(--accent-green); color: #000; font-weight: 700; font-size: 13px; border-radius: 50%; }
.step-num.fix-num { background: var(--accent-orange); }
.step-num.gen-num { background: var(--accent-purple); color: #fff; }
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
}
</style>
