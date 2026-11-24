<template>
  <div class="page">
    <div class="page-heading"><div><div class="eyebrow">{{ eyebrow }}</div><h1>{{ title }}</h1><p>{{ description }}</p></div>
      <el-button v-if="canCreate" type="primary" @click="openCreate"><el-icon><Plus /></el-icon>{{ createLabel || '新增' }}</el-button>
    </div>
    <section class="panel">
      <div class="toolbar">
        <el-input v-model="keyword" clearable placeholder="搜索关键词..." style="max-width:280px" @keyup.enter="load"><template #prefix><el-icon><Search /></el-icon></template></el-input>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
      </div>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column v-for="col in columns" :key="col.prop" :prop="col.prop" :label="col.label" :min-width="col.width || 130" show-overflow-tooltip>
          <template v-if="col.format" #default="{row}">{{ col.format(row[col.prop], row) }}</template>
          <template v-else-if="col.tag" #default="{row}"><el-tag :type="col.tag(row[col.prop])">{{ col.format ? col.format(row[col.prop],row) : row[col.prop] }}</el-tag></template>
        </el-table-column>
        <el-table-column v-if="canEdit || canDelete" label="操作" width="150" fixed="right">
          <template #default="{row}">
            <el-button v-if="canEdit" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm v-if="canDelete" title="确定删除这条记录？" @confirm="remove(row)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂无数据" /></template>
      </el-table>
      <div class="table-foot"><span>共 {{ total }} 条</span><el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[8, 15, 30]" :total="total" layout="total, sizes, prev, pager, next" @size-change="load" @current-change="load" /></div>
    </section>
    <el-dialog v-model="dialog" :title="editing ? '编辑' + title : '新增' + title" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item v-for="field in activeFields()" :key="field.key" :label="field.label" :prop="field.key">
          <el-select v-if="field.options" v-model="form[field.key]" :placeholder="`请选择${field.label}`" style="width:100%">
            <el-option v-for="op in field.options" :key="String(op.value)" :label="op.label" :value="op.value" />
          </el-select>
          <el-date-picker v-else-if="field.type==='date'" v-model="form[field.key]" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          <el-input v-else-if="field.type==='password'" v-model="form[field.key]" type="password" show-password />
          <el-input v-else v-model="form[field.key]" :type="field.type || 'text'" :placeholder="field.placeholder || `请输入${field.label}`" />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http, { errorMessage } from '../api/http'
import { listResource } from '../api/resources'

export type Field = { key:string; label:string; type?:string; placeholder?:string; options?:Array<{label:string;value:any}>; required?:boolean }
export type Column = { prop:string; label:string; width?:number; format?:(value:any,row:any)=>string; tag?:(value:any)=>any }
const props = defineProps<{
  title:string; eyebrow?:string; description:string; endpoint:string;
  columns:Column[]; fields?:Field[]; editFields?:Field[]; createPayload?:(form:any)=>any;
  updatePayload?:(form:any)=>any; canCreate?:boolean; canEdit?:boolean; canDelete?:boolean;
  createLabel?:string; searchParam?:string
}>()
const items = ref<any[]>([]), loading = ref(false), saving = ref(false), dialog = ref(false), editing = ref<any>(null), keyword = ref(''), page = ref(1), pageSize = ref(8), total = ref(0)
const form = reactive<Record<string,any>>({})
const formRef = ref()
const fields = props.fields || []
const activeFields = () => editing.value && props.editFields ? props.editFields : fields
const rules = Object.fromEntries(fields.filter(f=>f.required).map(f=>[f.key,[{required:true,message:`请填写${f.label}`,trigger:'blur'}]]))
async function load() {
  loading.value = true
  try {
    const params:any = {}
    if (keyword.value.trim()) params[props.searchParam || 'search'] = keyword.value.trim()
    params.page = page.value; params.page_size = pageSize.value
    const { data } = await http.get(props.endpoint, { params })
    items.value = Array.isArray(data) ? data : (data.results || [])
    total.value = Array.isArray(data) ? data.length : (data.count ?? items.value.length)
  } catch(e) { ElMessage.error(errorMessage(e)) }
  finally { loading.value = false }
}
function openCreate() {
  page.value = Math.max(1, page.value)
  editing.value = null
  Object.keys(form).forEach(k=>delete form[k])
  fields.forEach(f=>form[f.key]='')
  dialog.value = true
}
function openEdit(row:any) {
  editing.value = row
  Object.keys(form).forEach(k=>delete form[k])
  activeFields().forEach(f=>form[f.key]=row[f.key] ?? '')
  dialog.value = true
}
async function save() {
  try {
    await formRef.value.validate()
    saving.value = true
    const payload = props.createPayload ? props.createPayload({...form}) : {...form}
    if (editing.value) {
      const update = props.updatePayload ? props.updatePayload({...form}) : {...form}
      await http.patch(`${props.endpoint}${editing.value.id}/`, update)
    } else await http.post(props.endpoint, payload)
    ElMessage.success('保存成功'); dialog.value = false; await load()
  } catch(e:any) { if (e?.response) ElMessage.error(errorMessage(e)) }
  finally { saving.value = false }
}
async function remove(row:any) {
  try { await http.delete(`${props.endpoint}${row.id}/`); ElMessage.success('删除成功'); await load() }
  catch(e) { ElMessage.error(errorMessage(e)) }
}
onMounted(load)
</script>
