<template>
  <div class="page">
    <div class="welcome-row"><div><div class="eyebrow">OVERVIEW</div><h1>早上好，{{ auth.profile?.username || '用户' }} <span class="wave">✦</span></h1><p>欢迎回到实验室预约管理工作台，这里是你的业务概览。</p></div><el-button type="primary" @click="$router.push('/reservations')"><el-icon><Calendar /></el-icon> 查看预约</el-button></div>
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-top"><span>预约总数</span><span class="stat-icon blue"><el-icon><Tickets /></el-icon></span></div><strong>{{ stats.reservations }}</strong><small>当前可见的预约记录</small></div>
      <div class="stat-card"><div class="stat-top"><span>待审核</span><span class="stat-icon amber"><el-icon><Timer /></el-icon></span></div><strong>{{ stats.pending }}</strong><small>需要关注的申请</small></div>
      <div class="stat-card"><div class="stat-top"><span>实验室</span><span class="stat-icon violet"><el-icon><OfficeBuilding /></el-icon></span></div><strong>{{ stats.labs }}</strong><small>当前可见实验室</small></div>
      <div class="stat-card"><div class="stat-top"><span>可预约时段</span><span class="stat-icon green"><el-icon><Clock /></el-icon></span></div><strong>{{ stats.available }}</strong><small>状态为可预约</small></div>
    </div>
    <div class="dashboard-grid">
      <section class="panel"><div class="panel-heading"><div><h3>最近预约</h3><p>最近更新的预约申请</p></div><el-button text type="primary" @click="$router.push('/reservations')">查看全部 →</el-button></div>
        <el-table :data="recent" v-loading="loading" stripe>
          <el-table-column prop="id" label="编号" width="78" />
          <el-table-column label="预约时段" min-width="180"><template #default="{row}">时段 #{{ row.reservationtime }}</template></el-table-column>
          <el-table-column label="状态" width="110"><template #default="{row}"><el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag></template></el-table-column>
          <el-table-column prop="created_at" label="申请时间" min-width="160" />
        </el-table>
      </section>
      <section class="panel quick-panel"><div class="panel-heading"><div><h3>快捷入口</h3><p>常用功能</p></div></div>
        <div class="quick-link" @click="$router.push('/reservations')"><span class="quick-icon q-blue"><el-icon><Calendar /></el-icon></span><div><b>预约管理</b><small>查看、申请或审核预约</small></div><el-icon><ArrowRight /></el-icon></div>
        <div class="quick-link" v-if="auth.role !== 'student'" @click="$router.push('/labs')"><span class="quick-icon q-purple"><el-icon><OfficeBuilding /></el-icon></span><div><b>实验室管理</b><small>维护实验室信息</small></div><el-icon><ArrowRight /></el-icon></div>
        <div class="quick-link" v-if="auth.role === 'superuser'" @click="$router.push('/users')"><span class="quick-icon q-green"><el-icon><User /></el-icon></span><div><b>用户管理</b><small>查看系统用户</small></div><el-icon><ArrowRight /></el-icon></div>
      </section>
    </div>
    <div class="dashboard-foot">数据来自当前登录账号可访问的后端接口 · <a href="http://127.0.0.1:8000/api/docs/" target="_blank">API 文档</a></div>
  </div>
</template>
<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import http from '../api/http'
const auth = useAuthStore(), loading = ref(false), recent = ref<any[]>([])
const stats = reactive({ reservations: 0, pending: 0, labs: 0, available: 0 })
const rows = (d:any) => Array.isArray(d) ? d : (d?.results || [])
const statusText = (s:string) => ({pending:'待审核',approved:'已通过',rejected:'已拒绝',cancelled:'已取消'}[s] || s)
const statusType = (s:string) => ({pending:'warning',approved:'success',rejected:'danger',cancelled:'info'}[s] || 'info') as any
onMounted(async () => {
  loading.value = true
  const jobs = await Promise.allSettled([
    http.get('/reservations/', {params:{ordering:'-created_at',page_size:5}}), http.get('/labs/', {params:{page_size:1}}), http.get('/reservationtimes/', {params:{status:'available',page_size:1}}), http.get('/reservations/', {params:{status:'pending',page_size:1}})
  ])
  if (jobs[0].status === 'fulfilled') {
    const data = rows(jobs[0].value.data); stats.reservations = jobs[0].value.data.count ?? data.length
    recent.value = data.slice(0,5)
  }
  if (jobs[1].status === 'fulfilled') stats.labs = jobs[1].value.data.count ?? rows(jobs[1].value.data).length
  if (jobs[2].status === 'fulfilled') stats.available = jobs[2].value.data.count ?? rows(jobs[2].value.data).length
  if (jobs[3].status === 'fulfilled') stats.pending = jobs[3].value.data.count ?? rows(jobs[3].value.data).length
  loading.value = false
})
</script>
