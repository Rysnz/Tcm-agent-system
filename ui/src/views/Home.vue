<template>
  <div class="awwwards-home" @mousemove="handleMouseMove">
    <!-- Fluid Background Orbs -->
    <div class="ambient-bg">
      <div class="orb orb-1" :style="{ transform: `translate(${mouseX * 0.02}px, ${mouseY * 0.02}px)` }"></div>
      <div class="orb orb-2" :style="{ transform: `translate(${mouseX * -0.01}px, ${mouseY * -0.01}px)` }"></div>
      <div class="orb orb-3" :style="{ transform: `translate(${mouseX * 0.015}px, ${mouseY * -0.015}px)` }"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- Navigation / Header -->
    <header class="glass-nav">
      <div class="nav-logo">
        <div class="logo-mark"></div>
      </div>
      <div class="nav-actions">
        <button class="btn-ghost" @click="router.push('/wellness')">养生档案</button>
        <button class="btn-primary" @click="router.push('/consult')">进入系统</button>
      </div>
    </header>

    <main class="main-content">
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-badge">
          <span class="pulse-dot"></span>
          <span>Next-Gen TCM Agent Architecture</span>
        </div>
        <h1 class="hero-title">
          杏林语康<br />
          <span class="gradient-text">多体问诊引擎</span>
        </h1>
        <p class="hero-subtitle">
          基于大语言模型与多智能体架构，重构中医"望闻问切"全流程。<br />
          提供高精度、可追溯的辨证分析与全维度健康推演。
        </p>
        <div class="hero-cta">
          <button class="btn-glow" @click="router.push('/consult')">
            <span class="btn-text">开启智能诊断</span>
            <span class="btn-icon">→</span>
          </button>
          <button class="btn-outline" @click="router.push('/wellness')">
            查看个人态势
          </button>
        </div>
        <div class="hero-visual-container">
          <div class="glass-ring">
            <div class="core-ai">
              <div class="core-inner"></div>
            </div>
            <div class="orbit-node node-1">望</div>
            <div class="orbit-node node-2">闻</div>
            <div class="orbit-node node-3">问</div>
            <div class="orbit-node node-4">切</div>
          </div>
        </div>
      </section>

      <!-- Bento Box Features -->
      <section class="bento-section">
        <div class="section-title-wrap">
          <h2 class="section-title">全域矩阵能力</h2>
          <div class="title-line"></div>
        </div>
        <div class="bento-grid">
          <div class="glass-card span-2 hover-glow" @click="router.push('/consult')">
            <div class="card-icon">🩺</div>
            <h3>多智能体协同流水线</h3>
            <p>七大专业 Agent 深度协作，动态覆盖接诊、追问、望诊到辨证与合规建议的全生命周期计算。</p>
          </div>
          <div class="glass-card hover-glow" @click="router.push('/consult/tongue')">
            <div class="card-icon">👅</div>
            <h3>多模态视觉解析</h3>
            <p>毫秒级提取舌象/面色视觉特征，结构化对齐中医诊断流。</p>
          </div>
          <div class="glass-card hover-glow" @click="router.push('/wellness')">
            <div class="card-icon">🌿</div>
            <h3>自适应健康推演</h3>
            <p>根据体质与时令生成四维周期计划，持续反馈迭代。</p>
          </div>
          <div class="glass-card span-2 highlight hover-glow">
            <div class="card-icon">📚</div>
            <h3>RAG 神经知识增强</h3>
            <p>向量与 BM25 混合检索中医典籍与权威数据，双路校验确保每一条诊疗结论的极高可溯源性。</p>
          </div>
        </div>
      </section>

      <!-- Agent Flow -->
      <section class="agent-section">
        <div class="section-title-wrap">
          <h2 class="section-title">量子级处理架构</h2>
        </div>
        <div class="agent-flow-container scroll-hide">
          <div class="agent-timeline">
            <div class="agent-node" v-for="(agent, i) in agents" :key="agent.name" :style="{'--delay': `${i * 0.1}s`}">
              <div class="node-icon-wrap">
                <span class="node-icon">{{ agent.emoji }}</span>
              </div>
              <div class="node-content">
                <div class="node-name">{{ agent.name }}</div>
                <div class="node-desc">{{ agent.desc }}</div>
              </div>
              <div class="connecting-line" v-if="i < agents.length - 1"></div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="glass-footer">
      <div class="footer-content">
        <div class="footer-brand">TCM Agent System</div>
        <div class="footer-legal">
          <span class="warning-icon">⚠️</span>
          本系统输出内容仅为健康建议与算法辨证参考，不构成任何医疗诊断。急重症请立即就医。
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 视差交互逻辑
const mouseX = ref(0)
const mouseY = ref(0)

const handleMouseMove = (e: MouseEvent) => {
  mouseX.value = e.clientX - window.innerWidth / 2
  mouseY.value = e.clientY - window.innerHeight / 2
}

const agents = [
  { emoji: '📋', name: 'Intake',         desc: '态势分诊' },
  { emoji: '💬', name: 'Inquiry',        desc: '智能追问' },
  { emoji: '👁',  name: 'Observation',   desc: '多模融合' },
  { emoji: '🔬', name: 'Syndrome',       desc: '辨证推演' },
  { emoji: '💊', name: 'Recommendation', desc: '调理生成' },
  { emoji: '🛡',  name: 'SafetyGuard',   desc: '合规熔断' },
  { emoji: '📝', name: 'Report',         desc: '终端报告' },
]
</script>

<style scoped>
:root {
  --abyss: var(--tcm-bg-color, #050505);
  --surface: var(--tcm-card-bg, rgba(255, 255, 255, 0.03));
  --surface-hover: var(--tcm-card-bg, rgba(255, 255, 255, 0.08));
  --border: var(--tcm-border-color, rgba(255, 255, 255, 0.08));
  --border-light: var(--tcm-border-color, rgba(255, 255, 255, 0.15));
  --text-main: var(--tcm-text-primary, #ffffff);
  --text-muted: var(--tcm-text-regular, #a1a1aa);
  
  --emerald: var(--tcm-accent-color, #10b981);
  --teal: var(--tcm-accent-color, #14b8a6);
  --purple: var(--tcm-accent-color, #8b5cf6);
}

.awwwards-home {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background: var(--tcm-ambient-gradient, var(--tcm-bg-color, #050505)); /* Fallback */
  color: var(--tcm-text-primary, #ffffff);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  overflow-x: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 沉浸式流体背景 */
.ambient-bg {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  background: var(--tcm-ambient-gradient);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.5;
  animation: float 20s infinite ease-in-out alternate;
  transition: transform 0.1s ease-out; /* 响应鼠标视差 */
}

.orb-1 { top: -10%; left: -10%; width: 50vw; height: 50vw; background: radial-gradient(circle, rgba(20,184,166,0.4) 0%, rgba(0,0,0,0) 70%); }
.orb-2 { bottom: -20%; right: -10%; width: 60vw; height: 60vw; background: radial-gradient(circle, rgba(139,92,246,0.3) 0%, rgba(0,0,0,0) 70%); animation-delay: -5s; }
.orb-3 { top: 40%; left: 40%; width: 40vw; height: 40vw; background: radial-gradient(circle, rgba(16,185,129,0.2) 0%, rgba(0,0,0,0) 70%); animation-delay: -10s; }

.noise-overlay {
  position: absolute; inset: 0;
  background: url('data:image/svg+xml;utf8,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E');
  mix-blend-mode: overlay;
}

@keyframes float {
  0% { transform: scale(1) translate(0, 0); }
  50% { transform: scale(1.1) translate(2%, 2%); }
  100% { transform: scale(0.9) translate(-2%, -2%); }
}

/* 玻璃拟态导航栏 */
.glass-nav {
  position: fixed; top: 0; left: 0; right: 0; padding: 20px 40px;
  display: flex; justify-content: space-between; align-items: center;
  z-index: 100; background: var(--tcm-card-bg, rgba(5, 5, 5, 0.4));
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.08));
  box-sizing: border-box;
}

.nav-logo { display: flex; align-items: center; gap: 12px; font-weight: 700; letter-spacing: 1px; }
.logo-mark { width: 24px; height: 24px; background: linear-gradient(135deg, #14b8a6, #8b5cf6); border-radius: 6px; box-shadow: 0 0 15px rgba(20, 184, 166, 0.5); }
.nav-actions { display: flex; gap: 16px; }

button { all: unset; cursor: pointer; box-sizing: border-box; }
.btn-ghost { color: var(--tcm-text-regular, #a1a1aa); font-size: 14px; padding: 8px 16px; transition: color 0.3s; }
.btn-ghost:hover { color: var(--tcm-text-primary, #ffffff); }
.btn-primary { background: var(--tcm-text-primary, #ffffff); color: var(--tcm-bg-color, #050505); padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 600; transition: transform 0.3s, box-shadow 0.3s; }
.btn-primary:hover { transform: scale(1.05); box-shadow: var(--tcm-shadow, 0 0 20px rgba(255,255,255,0.3)); }

/* 主内容区 */
.main-content { position: relative; z-index: 10; padding-top: 120px; max-width: 1200px; margin: 0 auto; }
.hero-section { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 60px 20px; }

.hero-badge {
  display: inline-flex; align-items: center; gap: 8px; padding: 6px 16px;
  background: var(--tcm-card-bg, rgba(255, 255, 255, 0.03)); border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.08)); border-radius: 100px;
  font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 32px; backdrop-filter: blur(10px);
}
.pulse-dot { width: 6px; height: 6px; background: var(--tcm-accent-color, #10b981); border-radius: 50%; box-shadow: 0 0 10px var(--tcm-accent-color, #10b981); animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { box-shadow: 0 0 0 10px transparent; } 100% { box-shadow: 0 0 0 0 transparent; } }

.hero-title { font-size: clamp(3rem, 6vw, 5rem); font-weight: 800; line-height: 1.1; margin: 0 0 24px; letter-spacing: -0.02em; }
.gradient-text { background: linear-gradient(to right, var(--tcm-text-primary, #fff), var(--teal), var(--purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-subtitle { font-size: clamp(1rem, 1.5vw, 1.25rem); color: var(--tcm-text-regular, #a1a1aa); max-width: 600px; line-height: 1.6; margin: 0 0 40px; }

/* 按钮与发光效果 */
.hero-cta { display: flex; gap: 20px; margin-bottom: 80px; flex-wrap: wrap; justify-content: center;}
.btn-glow {
  position: relative; display: inline-flex; align-items: center; gap: 12px;
  padding: 16px 32px; background: linear-gradient(135deg, rgba(20,184,166,0.2), rgba(139,92,246,0.2));
  border: 1px solid var(--tcm-border-color, rgba(255,255,255,0.1)); border-radius: 100px; color: var(--tcm-text-primary, #fff); font-size: 16px; font-weight: 600; overflow: hidden; transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}
.btn-glow::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); transition: left 0.5s ease; }
.btn-glow:hover { transform: translateY(-2px); box-shadow: var(--tcm-shadow, 0 10px 30px rgba(20, 184, 166, 0.3)); border-color: rgba(255,255,255,0.3); }
.btn-glow:hover::before { left: 100%; }

.btn-outline { padding: 16px 32px; border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.08)); border-radius: 100px; color: var(--tcm-text-primary, #ffffff); font-size: 16px; font-weight: 500; transition: all 0.3s ease; background: var(--tcm-card-bg, rgba(255, 255, 255, 0.03)); backdrop-filter: blur(10px); }
.btn-outline:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--tcm-border-color, rgba(255, 255, 255, 0.15)); }

/* 动态核心动画 - 望闻问切 */
.hero-visual-container { position: relative; width: 300px; height: 300px; margin: 0 auto; }
.glass-ring { position: absolute; inset: 0; border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.15)); border-radius: 50%; animation: spin-slow 30s linear infinite; }
.core-ai { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; background: var(--tcm-card-bg, rgba(255,255,255,0.05)); backdrop-filter: blur(20px); border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.15)); border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: var(--tcm-shadow, 0 0 40px rgba(20,184,166,0.4)), inset 0 0 20px rgba(255,255,255,0.1); }
.core-inner { width: 40px; height: 40px; background: radial-gradient(circle, var(--teal), var(--purple)); border-radius: 50%; filter: blur(5px); animation: pulse 3s infinite alternate; }
.orbit-node { position: absolute; width: 40px; height: 40px; background: var(--tcm-card-bg, rgba(255, 255, 255, 0.03)); border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.15)); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; backdrop-filter: blur(10px); box-shadow: var(--tcm-shadow, 0 0 15px rgba(0,0,0,0.5)); animation: spin-reverse 30s linear infinite; }
.node-1 { top: -20px; left: 130px; color: var(--teal); }
.node-2 { bottom: 130px; right: -20px; color: var(--emerald); }
.node-3 { bottom: -20px; left: 130px; color: var(--purple); }
.node-4 { top: 130px; left: -20px; color: var(--tcm-text-primary, #fff); }
@keyframes spin-slow { 100% { transform: rotate(360deg); } }
@keyframes spin-reverse { 100% { transform: rotate(-360deg); } }

/* 便当盒布局 */
.bento-section { padding: 80px 20px; }
.section-title-wrap { margin-bottom: 40px; }
.section-title { font-size: 2rem; font-weight: 700; margin: 0; }
.title-line { width: 60px; height: 2px; background: linear-gradient(90deg, var(--teal), transparent); margin-top: 12px; }

.bento-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; auto-rows: minmax(200px, auto); }
.glass-card { background: var(--tcm-card-bg, rgba(255, 255, 255, 0.03)); border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.08)); border-radius: 24px; padding: 32px; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1); display: flex; flex-direction: column; justify-content: flex-end; cursor: pointer; position: relative; overflow: hidden; }
.glass-card::after { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at center, rgba(255,255,255,0.05) 0%, transparent 60%); opacity: 0; transition: opacity 0.4s; }
.hover-glow:hover { transform: translateY(-5px); border-color: var(--tcm-border-color, rgba(255, 255, 255, 0.15)); box-shadow: var(--tcm-shadow, 0 20px 40px rgba(0,0,0,0.5)), 0 0 20px rgba(20,184,166,0.1); }
.hover-glow:hover::after { opacity: 1; }
.span-2 { grid-column: span 2; }
.card-icon { font-size: 2.5rem; margin-bottom: auto; }
.glass-card h3 { font-size: 1.25rem; margin: 16px 0 8px; font-weight: 600; }
.glass-card p { color: var(--tcm-text-regular, #a1a1aa); font-size: 0.95rem; line-height: 1.5; margin: 0; }
.highlight { background: linear-gradient(135deg, rgba(20,184,166,0.05), rgba(139,92,246,0.05)); border: 1px solid rgba(139,92,246,0.2); }

/* 流水线架构图 */
.agent-section { padding: 40px 20px 100px; }
.agent-flow-container { width: 100%; overflow-x: auto; padding-bottom: 20px; }
.scroll-hide::-webkit-scrollbar { display: none; }
.agent-timeline { display: flex; align-items: center; min-width: max-content; padding: 40px 0; }
.agent-node { display: flex; align-items: center; position: relative; animation: fade-in-right 0.8s var(--delay) backwards; }
.node-icon-wrap { width: 56px; height: 56px; background: var(--tcm-card-bg, rgba(255, 255, 255, 0.03)); border: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.15)); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; box-shadow: var(--tcm-shadow, 0 0 20px rgba(0,0,0,0.3)); z-index: 2; transition: transform 0.3s; }
.agent-node:hover .node-icon-wrap { transform: scale(1.1) rotate(5deg); border-color: var(--teal); box-shadow: 0 0 20px rgba(20,184,166,0.3); }
.node-content { margin-left: 16px; width: 100px; }
.node-name { font-weight: 600; font-size: 0.9rem; margin-bottom: 4px; }
.node-desc { font-size: 0.75rem; color: var(--tcm-text-regular, #a1a1aa); }
.connecting-line { width: 40px; height: 2px; background: linear-gradient(90deg, var(--tcm-border-color, rgba(255, 255, 255, 0.15)), transparent); margin: 0 16px; position: relative; }
.connecting-line::after { content: ''; position: absolute; top: 0; left: 0; width: 50%; height: 100%; background: var(--teal); box-shadow: 0 0 8px var(--teal); animation: flow 2s linear infinite; }
@keyframes flow { 0% { left: -50%; opacity: 0; } 50% { opacity: 1; } 100% { left: 100%; opacity: 0; } }
@keyframes fade-in-right { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }

/* 页脚 */
.glass-footer { border-top: 1px solid var(--tcm-border-color, rgba(255, 255, 255, 0.08)); padding: 40px 20px; background: var(--tcm-card-bg, rgba(5,5,5,0.8)); backdrop-filter: blur(20px); }
.footer-content { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 16px; text-align: center; }
.footer-brand { font-weight: 700; color: var(--tcm-text-regular, #a1a1aa); letter-spacing: 2px; text-transform: uppercase; font-size: 0.85rem; }
.footer-legal { font-size: 0.8rem; color: var(--tcm-text-regular, #666); max-width: 600px; line-height: 1.5; }
.warning-icon { color: var(--teal); margin-right: 4px; }

/* 响应式 */
@media (max-width: 900px) {
  .bento-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: span 1; }
  .hero-title { font-size: 2.5rem; }
  .agent-timeline { padding: 20px 0; }
  .glass-nav { padding: 15px 20px; }
}
</style>
