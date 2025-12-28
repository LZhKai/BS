import request from './request'

export const getVehiclePage = (params) => {
  return request({
    url: '/vehicle/page',
    method: 'get',
    params
  })
}

export const getVehicleById = (id) => {
  return request({
    url: `/vehicle/${id}`,
    method: 'get'
  })
}

export const saveVehicle = (data) => {
  return request({
    url: '/vehicle',
    method: 'post',
    data
  })
}

export const updateVehicle = (id, data) => {
  return request({
    url: `/vehicle/${id}`,
    method: 'put',
    data
  })
}

export const deleteVehicle = (id) => {
  return request({
    url: `/vehicle/${id}`,
    method: 'delete'
  })
}

export const deleteVehicleBatch = (ids) => {
  return request({
    url: '/vehicle/batch',
    method: 'delete',
    data: ids
  })
}

export const getVehicleList = () => {
  return request({
    url: '/vehicle/list',
    method: 'get'
  })
}

