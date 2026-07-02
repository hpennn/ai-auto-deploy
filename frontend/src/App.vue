<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <span class="logo">🚀</span>
        <h1>AI Auto Deploy</h1>
        <span class="version">v1.0</span>
      </div>
      <div class="header-right">
        <el-tag type="success" effect="plain" round>
          <el-icon><Check /></el-icon>
          Web
        </el-tag>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Step 1: Project Path -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num">1</span>
          <span class="step-title">输入项目路径</span>
        </div>
        <div class="step-body">
          <el-input
            v-model="projectPath"
            placeholder="/path/to/your/project"
            size="large"
            clearable
            @keyup.enter="detectProject"
          >
            <template #prefix>
              <el-icon><Folder /></el-icon>
            </template>
            <template #append>
              <el-button
                type="primary"
                :loading="detecting"
                @click="detectProject"
              >
                <el-icon v-if="!detecting"><Search /></el-icon>
                检测
              </el-button>
            </template>
          </el-input>
        </div>
      </section>

      <!-- Step 2: Project Info -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">2</span>
          <span class="step-title">项目信息</span>
        </div>
        <div class="step-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">📦 项目名称</span>
              <span class="info-value highlight">{{ projectInfo.project_name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">🏗️ 项目类型</span>
              <el-tag :type="typeTagColor(projectInfo.type)" effect="dark">
                {{ projectInfo.type }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">🔧 框架</span>
              <el-tag v-if="projectInfo.framework" type="info" effect="plain">
                {{ projectInfo.framework }}
              </el-tag>
              <span v-else class="info-value dim">-</span>
            </div>
            <div class="info-item">
              <span class="info-label">📋 包管理器</span>
              <el-tag v-if="projectInfo.package_manager" type="warning" effect="plain">
                {{ projectInfo.package_manager }}
              </el-tag>
              <span v-else class="info-value dim">-</span>
            </div>
            <div class="info-item">
              <span class="info-label">🐳 Docker</span>
              <el-tag :type="projectInfo.has_docker ? 'success' : 'info'" effect="plain">
                {{ projectInfo.has_docker ? '已配置' : '未配置' }}
              </el-tag>
            </div>
            <div class="info-item" v-if="projectInfo.entry_point">
              <span class="info-label">🔗 入口</span>
              <span class="info-value code">{{ projectInfo.entry_point }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 3: Deploy Configuration -->
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
                <el-option
                  v-for="opt in deployOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                >
                  <span>{{ opt.icon }} {{ opt.label }}</span>
                </el-option>
              </el-select>
            </div>
            <div class="config-item" v-if="deployType === 'server' && servers.length > 0">
              <label>目标服务器</label>
              <el-select v-model="selectedServerIdx" placeholder="选择服务器" size="large" style="width:100%">
                <el-option
                  v-for="(s, i) in servers"
                  :key="i"
                  :label="`${s.name} (${s.host})`"
                  :value="i"
                />
              </el-select>
            </div>
            <div class="config-item" v-if="deployType === 'server'">
              <label>域名/IP</label>
              <el-input v-model="domain" placeholder="example.com 或 IP" size="large" />
            </div>
          </div>
        </div>
      </section>

      <!-- Step 4: Generate -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">4</span>
          <span class="step-title">生成部署脚本</span>
        </div>
        <div class="step-body">
          <el-button
            type="primary"
            size="large"
            :loading="generating"
            @click="generateScript"
          >
            <el-icon v-if="!generating"><VideoPlay /></el-icon>
            生成脚本
          </el-button>

          <!-- Terminal Output -->
          <div v-if="scriptOutput" class="terminal-container fade-in">
            <div class="terminal-header">
              <div class="terminal-dots">
                <span class="dot red"></span>
                <span class="dot yellow"></span>
                <span class="dot green"></span>
              </div>
              <span class="terminal-title">{{ scriptFilename }}</span>
              <div class="terminal-actions">
                <el-button text size="small" @click="copyScript">
                  <el-icon><CopyDocument /></el-icon>
                  {{ copied ? '已复制!' : '复制' }}
                </el-button>
                <el-button text size="small" @click="downloadScript">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
              </div>
            </div>
            <div class="terminal-body">
              <pre><code>{{ scriptOutput }}</code></pre>
            </div>
          </div>

          <!-- Extra files -->
          <div v-if="extraFiles.length > 0" class="extra-files fade-in">
            <h4>📎 附加文件</h4>
            <div v-for="file in extraFiles" :key="file.filename" class="extra-file-item">
              <div class="extra-file-header">
                <span>{{ file.filename }}</span>
                <el-button text size="small" @click="copyExtra(file.content)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button text size="small" @click="downloadExtra(file)">
                  <el-icon><Download /></el-icon>
                </el-button>
              </div>
              <div class="terminal-body compact">
                <pre><code>{{ file.content }}</code></pre>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <span>AI Auto Deploy</span>
      <span class="separator">·</span>
      <span>智能识别 · 一键部署 · 多平台支持</span>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
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
    }
  },
  mounted() {
    this.loadServers()
  },
  methods: {
    async detectProject() {
      if (!this.projectPath.trim()) {
        this.$message.warning('请输入项目路径')
        return
      }
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
      } finally {
        this.detecting = false
      }
    },

    async generateScript() {
      this.generating = true
      this.scriptOutput = ''
      this.extraFiles = []
      try {
        const payload = {
          path: this.projectPath,
          deploy_type: this.deployType,
          domain: this.domain || undefined,
        }
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
      } finally {
        this.generating = false
      }
    },

    async loadServers() {
      try {
        const res = await axios.get('/api/servers')
        this.servers = res.data.servers || []
      } catch {
        this.servers = []
      }
    },

    copyScript() {
      navigator.clipboard.writeText(this.scriptOutput)
      this.copied = true
      setTimeout(() => { this.copied = false }, 2000)
    },

    copyExtra(content) {
      navigator.clipboard.writeText(content)
      this.$message.success('已复制')
    },

    downloadScript() {
      this.downloadFile(this.scriptFilename, this.scriptOutput)
    },

    downloadExtra(file) {
      this.downloadFile(file.filename, file.content)
    },

    downloadFile(filename, content) {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },

    typeTagColor(type) {
      const map = { python: 'success', nodejs: 'warning', static: 'info' }
      return map[type] || ''
    },
  },
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px;
}

/* Header */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 0;
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  font-size: 28px;
}

.header-left h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.version {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 10px;
}

/* Main */
.main-content {
  flex: 1;
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Step Section */
.step-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.step-num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-green);
  color: #000;
  font-weight: 700;
  font-size: 13px;
  border-radius: 50%;
}

.step-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.step-body {
  padding: 20px;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  font-weight: 500;
}

.info-value.highlight {
  color: var(--accent-blue);
}

.info-value.code {
  font-family: monospace;
  color: var(--accent-green);
}

.info-value.dim {
  color: var(--text-secondary);
}

/* Config Row */
.config-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.config-item {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* Terminal */
.terminal-container {
  margin-top: 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.terminal-dots {
  display: flex;
  gap: 6px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: #ff5f57; }
.dot.yellow { background: #febc2e; }
.dot.green { background: #28c840; }

.terminal-title {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}

.terminal-actions {
  display: flex;
  gap: 4px;
}

.terminal-body {
  background: var(--terminal-bg);
  padding: 16px;
  max-height: 500px;
  overflow: auto;
}

.terminal-body.compact {
  max-height: 300px;
}

.terminal-body pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
  color: var(--terminal-green);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Extra files */
.extra-files {
  margin-top: 16px;
}

.extra-files h4 {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.extra-file-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}

.extra-file-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  font-size: 13px;
  color: var(--text-primary);
}

/* Footer */
.app-footer {
  padding: 20px 0;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  border-top: 1px solid var(--border-color);
}

.separator {
  margin: 0 8px;
}

/* Animations */
.fade-in {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive */
@media (max-width: 600px) {
  .app-container {
    padding: 0 12px;
  }
  .info-grid {
    grid-template-columns: 1fr;
  }
  .config-row {
    flex-direction: column;
  }
}
</style>
