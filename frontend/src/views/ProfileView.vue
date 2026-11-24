<template>
  <div class="page">
    <div class="page-heading"><div><div class="eyebrow">ACCOUNT</div><h1>个人资料</h1><p>查看并修改当前账号的联系信息。</p></div></div>
    <section class="panel profile-panel">
      <div class="profile-avatar">{{ (auth.profile?.username||'U').slice(0,1).toUpperCase() }}</div>
      <div class="profile-meta"><h3>{{ auth.profile?.username }}</h3><el-tag>{{ roleLabel }}</el-tag><p>账号 ID：{{ auth.profile?.id ?? '-' }}</p></div>
      <el-divider />
      <el-form label-position="top" class="profile-form">
        <el-form-item label="用户名"><el-input :model-value="auth.profile?.username" disabled /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
      </el-form>
    </section>
  </div>
</template>
<script setup lang="ts">
import {computed,onMounted,reactive,ref} from 'vue'
import {ElMessage} from 'element-plus'
import http,{errorMessage} from '../api/http'
import {useAuthStore} from '../stores/auth'
const auth=useAuthStore(),saving=ref(false),form=reactive({email:'',phone:''})
const roleLabel=computed(()=>({superuser:'超级管理员',student:'学生',labadmin:'实验室管理员',unknown:'普通用户'}[auth.role]))
onMounted(()=>{form.email=auth.profile?.email||'';form.phone=auth.profile?.phone||''})
async function save(){saving.value=true;try{const {data}=await http.patch('/users/me/',form);auth.profile=data.user||data;ElMessage.success('资料已更新')}catch(e){ElMessage.error(errorMessage(e))}finally{saving.value=false}}
</script>
