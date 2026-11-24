<template>
  <div class="page">
    <div class="page-heading"><div><div class="eyebrow">SYSTEM ADMIN</div><h1>用户管理</h1><p>超级管理员可查看用户账号并执行软删除。</p></div></div>
    <section class="panel">
      <div class="toolbar"><el-input v-model="search" clearable placeholder="搜索用户名、邮箱或手机号" style="max-width:320px" @keyup.enter="load" /><el-button @click="load">搜索</el-button></div>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="90"/><el-table-column prop="username" label="用户名" min-width="180"/><el-table-column prop="email" label="邮箱" min-width="200"/><el-table-column prop="phone" label="手机号" min-width="150"/>
        <el-table-column label="操作" width="120"><template #default="{row}"><el-popconfirm title="确定删除该用户？关联业务档案也会按后端规则处理。" @confirm="remove(row)"><template #reference><el-button link type="danger">删除用户</el-button></template></el-popconfirm></template></el-table-column>
        <template #empty><el-empty description="暂无用户"/></template>
      </el-table>
      <div class="table-foot"><span>共 {{ total }} 条用户</span><el-pagination v-model:current-page="page" :page-size="8" :total="total" layout="total, prev, pager, next" @current-change="load" /></div>
    </section>
  </div>
</template>
<script setup lang="ts">
import { onMounted,ref } from 'vue'
import {ElMessage} from 'element-plus'
import http,{errorMessage} from '../api/http'
const items=ref<any[]>([]),loading=ref(false),search=ref(''),page=ref(1),total=ref(0)
async function load(){loading.value=true;try{const {data}=await http.get('/users/',{params:{page:page.value,page_size:8,...(search.value?{search:search.value}:{})}});items.value=Array.isArray(data)?data:(data.results||[]);total.value=data.count??items.value.length}catch(e){ElMessage.error(errorMessage(e))}finally{loading.value=false}}
async function remove(row:any){try{await http.delete(`/users/${row.id}/`);ElMessage.success('用户已删除');await load()}catch(e){ElMessage.error(errorMessage(e))}}
onMounted(load)
</script>
