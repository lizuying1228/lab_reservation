<template>
  <ResourcePage title="实验室管理" eyebrow="RESOURCE CENTER" description="维护实验室基础信息、开放状态与负责人。" endpoint="/labs/" :columns="columns" :fields="fields" :can-create="auth.role==='superuser' || auth.role === 'labadmin'" :can-edit="auth.role==='superuser'" :can-delete="auth.role==='superuser'" />
</template>
<script setup lang="ts">
import ResourcePage from '../components/ResourcePage.vue'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
const columns = [
 {prop:'id',label:'ID',width:75},{prop:'lab_no',label:'实验室编号'},
 {prop:'position',label:'地点'},
 {prop:'labadmin',label:'管理员',format:(v:any)=>typeof v==='object'?(v?.name || v?.admin_no || '-'):(v ?? '-')},
 {prop:'status',label:'状态',format:(v:string)=>({open:'开放',closed:'关闭',maintenance:'维修'}[v]||v)}
]
const fields = [
 {key:'lab_no',label:'实验室编号',required:true},
 {key:'position',label:'实验室地点',required:true},
 {key:'labadmin_admin_no',label:'管理员编号',required:true},
 {key:'status',label:'状态',options:[{label:'开放',value:'open'},{label:'关闭',value:'closed'},{label:'维修',value:'maintenance'}],required:true}
]
</script>
