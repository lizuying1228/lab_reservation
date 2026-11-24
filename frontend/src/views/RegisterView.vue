<template>
  <div class="auth-page">
    <div class="auth-art"><div class="art-orbit orbit-one"></div><div class="art-orbit orbit-two"></div><div class="art-copy"><div class="art-logo"><el-icon><OfficeBuilding /></el-icon></div><h1>开启更高效的<br/>实验室协作。</h1><p>创建账号后，可由系统管理员为你建立学生或管理员档案。</p><div class="art-bottom">LABSPACE · SMART CAMPUS</div></div></div>
    <div class="auth-form-wrap"><div class="auth-form">
      <div class="eyebrow">CREATE ACCOUNT</div><h2>创建账号</h2><p class="muted">注册普通用户账号，身份档案由管理员分配。</p>
      <el-form label-position="top" size="large">
        <el-form-item label="用户名"><el-input v-model="form.username" placeholder="请输入用户名" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password placeholder="至少 8 位" /></el-form-item>
        <el-form-item label="邮箱（选填）"><el-input v-model="form.email" placeholder="name@example.com" /></el-form-item>
        <el-form-item label="手机号（选填）"><el-input v-model="form.phone" placeholder="请输入手机号" /></el-form-item>
        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">注 册 <el-icon><ArrowRight /></el-icon></el-button>
      </el-form>
      <div class="auth-switch">已有账号？<router-link to="/login">返回登录</router-link></div>
    </div></div>
  </div>
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http, { errorMessage } from '../api/http'
const router = useRouter(), loading = ref(false)
const form = reactive({ username: '', password: '', email: '', phone: '' })
async function submit() {
  if (!form.username || form.password.length < 8) return ElMessage.warning('用户名必填，密码至少 8 位')
  loading.value = true
  try { await http.post('/users/register/', form); ElMessage.success('注册成功，请登录'); router.push('/login') }
  catch (e) { ElMessage.error(errorMessage(e)) }
  finally { loading.value = false }
}
</script>
