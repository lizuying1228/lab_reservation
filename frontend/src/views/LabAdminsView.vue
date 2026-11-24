<template>
  <ResourcePage title="实验室管理员" eyebrow="PEOPLE" description="创建和维护实验室管理员档案及其账号。" endpoint="/labadmins/" :columns="columns" :fields="fields" :edit-fields="editFields" :can-create="true" :can-edit="true" :can-delete="true" />
</template>
<script setup lang="ts">
import ResourcePage from '../components/ResourcePage.vue'
const columns=[{prop:'id',label:'ID',width:70},{prop:'name',label:'姓名'},{prop:'admin_no',label:'管理员编号'},{prop:'birth_date',label:'出生日期'},{prop:'user',label:'用户账号',format:(v:any)=>typeof v==='object'?v?.username:(v??'-')}]
const fields=[{key:'name',label:'姓名',required:true},{key:'admin_no',label:'管理员编号',required:true},{key:'birth_date',label:'出生日期',type:'date',required:true},{key:'username',label:'登录用户名',required:true},{key:'password',label:'初始密码（至少 8 位）',type:'password',required:true}]
const editFields=[{key:'name',label:'姓名',required:true},{key:'birth_date',label:'出生日期',type:'date',required:true}]
</script>
