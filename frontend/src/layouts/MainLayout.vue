<template>
  <el-container class="shell">
    <el-aside width="238px" class="sidebar">
      <div class="brand">
        <div class="brand-mark"><el-icon><OfficeBuilding /></el-icon></div>
        <div><strong>LabSpace</strong><small>实验室预约管理系统</small></div>
      </div>
      <div class="menu-label">工作空间</div>
      <el-menu router :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/reservations"><el-icon><Calendar /></el-icon><span>预约管理</span></el-menu-item>
        <template v-if="auth.role !== 'student'">
          <div class="menu-label">资源管理</div>
          <el-menu-item index="/labs"><el-icon><OfficeBuilding /></el-icon><span>实验室管理</span></el-menu-item>
          <el-menu-item index="/times"><el-icon><Clock /></el-icon><span>预约时段</span></el-menu-item>
          <el-menu-item index="/students"><el-icon><User /></el-icon><span>学生管理</span></el-menu-item>
        </template>
        <template v-if="auth.role === 'superuser'">
          <div class="menu-label">系统管理</div>
          <el-menu-item index="/labadmins"><el-icon><Avatar /></el-icon><span>管理员管理</span></el-menu-item>
          <el-menu-item index="/users"><el-icon><Setting /></el-icon><span>用户管理</span></el-menu-item>
        </template>
      </el-menu>
      <div class="sidebar-bottom">
        <div class="help-card"><span class="help-icon">✦</span><b>需要帮助？</b><p>查看接口文档了解系统功能。</p><a href="http://127.0.0.1:8000/api/docs/" target="_blank">打开 API 文档 ↗</a></div>
        <div class="side-foot">LABSPACE · MANAGEMENT</div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <div class="crumb">工作空间 <span>/</span> {{ $route.meta.title || '工作台' }}</div>
        <div class="top-actions">
          <el-tag effect="plain" round>{{ roleLabel }}</el-tag>
          <el-dropdown>
            <div class="user-trigger"><el-avatar :size="34">{{ (auth.profile?.username || 'U').slice(0,1).toUpperCase() }}</el-avatar><span>{{ auth.profile?.username || '用户' }}</span><el-icon><ArrowDown /></el-icon></div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/profile')">个人资料</el-dropdown-item>
                <el-dropdown-item divided @click="signOut">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
const router = useRouter()
const roleLabel = computed(() => ({ superuser: '超级管理员', student: '学生', labadmin: '实验室管理员', unknown: '用户' }[auth.role]))
async function signOut() {
  try { await auth.logout() } catch { auth.clearLocal() }
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>
