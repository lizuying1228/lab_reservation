<template>
  <ResourcePage title="学生管理" eyebrow="PEOPLE" description="管理学生档案。新建档案时可绑定已有账号，或同时创建新账号。" endpoint="/students/" :columns="columns" :fields="fields" :edit-fields="editFields" :create-payload="createPayload" :can-create="auth.role==='superuser'" :can-edit="true" :can-delete="auth.role==='superuser'" />
</template>
<script setup lang="ts">
import ResourcePage from '../components/ResourcePage.vue'
import { useAuthStore } from '../stores/auth'
const auth=useAuthStore()
const columns=[{prop:'id',label:'ID',width:70},{prop:'name',label:'姓名'},{prop:'student_no',label:'学号'},{prop:'birth_date',label:'出生日期'},{prop:'user',label:'用户账号',format:(v:any)=>typeof v==='object'?v?.username:(v??'-')}]
const fields=[{key:'name',label:'姓名',required:true},{key:'student_no',label:'学号',required:true},{key:'birth_date',label:'出生日期',type:'date',required:true},{key:'user_id',label:'已有用户 ID（绑定已有账号时填写）'},{key:'username',label:'新用户用户名（创建新账号时填写）'},{key:'password',label:'新用户密码（至少 8 位）',type:'password'}]
const editFields=[{key:'name',label:'姓名',required:true},{key:'birth_date',label:'出生日期',type:'date',required:true}]
function createPayload(form:any){const data:any={name:form.name,student_no:form.student_no,birth_date:form.birth_date};if(form.user_id)data.user_id=Number(form.user_id);else{data.username=form.username;data.password=form.password;}return data}
</script>
