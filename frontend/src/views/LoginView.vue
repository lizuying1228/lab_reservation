<template>
  <div class="auth-page">
    <div class="auth-art">
      <div class="art-orbit orbit-one"></div><div class="art-orbit orbit-two"></div>
      <div class="art-copy"><div class="art-logo"><el-icon><OfficeBuilding /></el-icon></div><h1>让每一次实验<br/>都井然有序。</h1><p>统一管理实验室资源，让预约、审核与使用安排更加简单高效。</p><div class="art-bottom">LABSPACE · SMART CAMPUS</div></div>
    </div>
    <div class="auth-form-wrap">
      <div class="auth-form">
        <div class="mobile-brand">LABSPACE</div><div class="eyebrow">WELCOME BACK</div>
        <h2>欢迎回来</h2><p class="muted">登录你的账号，继续管理实验室预约。</p>
        <el-form @submit.prevent="submit" label-position="top" size="large">
          <el-form-item label="用户名"><el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" @keyup.enter="submit" /></el-form-item>
          <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">登 录 <el-icon><ArrowRight /></el-icon></el-button>
        </el-form>
        <div class="auth-switch">还没有账号？<router-link to="/register">立即注册</router-link></div>
        <div class="auth-note">登录即表示你同意遵守实验室预约管理规定。</div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { errorMessage } from '../api/http'
const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
async function submit() {
  if (!form.username || !form.password) return ElMessage.warning('请输入用户名和密码')
  loading.value = true
  try { await auth.login(form.username, form.password); ElMessage.success('登录成功'); router.push('/dashboard') }
  catch (e) { ElMessage.error(errorMessage(e)) }
  finally { loading.value = false }
}
</script>
