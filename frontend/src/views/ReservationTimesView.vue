<template>
  <ResourcePage title="预约时段" eyebrow="SCHEDULE" description="管理未来可预约日期的实验室时段。" endpoint="/reservationtimes/" :columns="columns" :fields="fields" :can-create="true" :can-edit="false" :can-delete="true" />
</template>
<script setup lang="ts">
import ResourcePage from '../components/ResourcePage.vue'
const columns = [
 {prop:'id',label:'ID',width:75},
 {prop:'lab',label:'实验室',format:(v:any)=>typeof v==='object'?(v?.lab_no || v?.id):(v ?? '-')},
 {prop:'date',label:'预约日期'},
 {prop:'time',label:'时段',format:(v:string)=>({morning:'上午',afternoon:'下午',evening:'晚上'}[v]||v)},
 {prop:'status',label:'状态',format:(v:string)=>({available:'可预约',occupied:'已占用'}[v]||v)}
]
const fields = [
 {key:'lab_no',label:'实验室编号',required:true},
 {key:'date',label:'预约日期',type:'date',required:true},
 {key:'time',label:'时段',options:[{label:'上午',value:'morning'},{label:'下午',value:'afternoon'},{label:'晚上',value:'evening'}],required:true}
]
</script>
