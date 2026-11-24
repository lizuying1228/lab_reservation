<template>
  <div class="page">
    <div class="page-heading"><div><div class="eyebrow">BOOKING CENTER</div><h1>预约管理</h1><p>查看预约申请进度，学生可申请或取消，管理员可审核申请。</p></div>
      <el-button v-if="auth.role==='student'" type="primary" @click="openApply"><el-icon><Plus /></el-icon>申请预约</el-button>
    </div>
    <section class="panel">
      <div class="toolbar"><el-input v-model="search" clearable placeholder="搜索预约编号 / 学生 / 实验室" style="max-width:300px" @keyup.enter="load"><template #prefix><el-icon><Search /></el-icon></template></el-input><el-select v-model="status" clearable placeholder="全部状态" style="width:150px" @change="load"><el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" /></el-select><el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button></div>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="预约编号" width="100" />
        <el-table-column label="学生" min-width="140"><template #default="{row}">{{ display(row.student) }}</template></el-table-column>
        <el-table-column label="预约时段" min-width="180"><template #default="{row}">{{ display(row.reservationtime) }}</template></el-table-column>
        <el-table-column prop="status" label="状态" width="110"><template #default="{row}"><el-tag :type="tagType(row.status)">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="created_at" label="申请时间" min-width="180" />
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{row}">
            <el-button v-if="canReview && row.status==='pending'" link type="success" @click="review(row,'approved')">通过</el-button>
            <el-button v-if="canReview && row.status==='pending'" link type="danger" @click="review(row,'rejected')">拒绝</el-button>
            <el-popconfirm v-if="auth.role==='student' && ['pending','approved'].includes(row.status)" title="确定取消这条预约？" @confirm="cancel(row)"><template #reference><el-button link type="warning">取消</el-button></template></el-popconfirm>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂无预约记录" /></template>
      </el-table>
      <div class="table-foot"><span>共 {{ total }} 条记录</span><el-pagination v-model:current-page="page" :page-size="8" :total="total" layout="total, prev, pager, next" @current-change="load" /></div>
    </section>
    <el-dialog v-model="applyDialog" title="申请预约" width="520px">
      <el-form label-position="top"><el-form-item label="选择预约时段"><el-select v-model="reservationtimeId" filterable placeholder="请选择可预约时段" style="width:100%"><el-option v-for="t in availableTimes" :key="t.id" :value="t.id" :label="timeLabel(t)" /></el-select></el-form-item></el-form>
      <template #footer><el-button @click="applyDialog=false">取消</el-button><el-button type="primary" :loading="saving" @click="apply">提交申请</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http, { errorMessage } from '../api/http'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore(), items=ref<any[]>([]), loading=ref(false), saving=ref(false)
const search=ref(''), status=ref(''), applyDialog=ref(false), reservationtimeId=ref<number|undefined>(), availableTimes=ref<any[]>([]), page=ref(1), total=ref(0)
const statuses=[{label:'待审核',value:'pending'},{label:'已通过',value:'approved'},{label:'已拒绝',value:'rejected'},{label:'已取消',value:'cancelled'}]
const canReview=computed(()=>auth.role==='labadmin'||auth.role==='superuser')
const statusLabel=(s:string)=>({pending:'待审核',approved:'已通过',rejected:'已拒绝',cancelled:'已取消'}[s]||s)
const tagType=(s:string)=>({pending:'warning',approved:'success',rejected:'danger',cancelled:'info'}[s]||'info') as any
const display=(v:any)=>typeof v==='object'?(v?.name || v?.lab_no || v?.id || '-'):(v ?? '-')
const rows=(d:any)=>Array.isArray(d)?d:(d?.results||[])
async function load(){
  loading.value=true
  try { const params:any={page:page.value,page_size:8}; if(status.value)params.status=status.value; if(search.value)params.search=search.value
    const {data}=await http.get('/reservations/',{params}); items.value=rows(data); total.value=data.count ?? items.value.length
  } catch(e){ElMessage.error(errorMessage(e))} finally{loading.value=false}
}
const timeLabel=(t:any)=>`#${t.id} · ${display(t.lab)} · ${t.date} · ${{morning:'上午',afternoon:'下午',evening:'晚上'}[t.time]||t.time}`
async function openApply(){
  try{const {data}=await http.get('/reservationtimes/',{params:{status:'available'}});availableTimes.value=rows(data).filter((x:any)=>x.status==='available');reservationtimeId.value=undefined;applyDialog.value=true}
  catch(e){ElMessage.error(errorMessage(e))}
}
async function apply(){
  if(!reservationtimeId.value)return ElMessage.warning('请选择预约时段')
  saving.value=true
  try{await http.post('/reservations/',{reservationtime_id:reservationtimeId.value});ElMessage.success('预约申请已提交');applyDialog.value=false;await load()}
  catch(e){ElMessage.error(errorMessage(e))}finally{saving.value=false}
}
async function review(row:any,target:string){
  const label=target==='approved'?'通过':'拒绝'
  try{await ElMessageBox.confirm(`确定${label}预约 #${row.id}？`,'审核确认');await http.patch(`/reservations/${row.id}/review/`,{status:target});ElMessage.success(`已${label}`);await load()}
  catch(e:any){if(e!=='cancel'&&e!=='close')ElMessage.error(errorMessage(e))}
}
async function cancel(row:any){
  try{await http.patch(`/reservations/${row.id}/cancel/`,{});ElMessage.success('预约已取消');await load()}
  catch(e){ElMessage.error(errorMessage(e))}
}
onMounted(load)
</script>
