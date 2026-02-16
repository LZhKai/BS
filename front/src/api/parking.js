import request from './request'

export const getParkingPage = (params) => {
  return request({
    url: '/parking/page',
    method: 'get',
    params
  })
}

export const getParkingById = (id) => {
  return request({
    url: `/parking/${id}`,
    method: 'get'
  })
}

export const saveParking = (data) => {
  return request({
    url: '/parking',
    method: 'post',
    data
  })
}

export const updateParking = (id, data) => {
  return request({
    url: `/parking/${id}`,
    method: 'put',
    data
  })
}

export const deleteParking = (id) => {
  return request({
    url: `/parking/${id}`,
    method: 'delete'
  })
}

export const getParkingList = (params) => {
  return request({
    url: '/parking/list',
    method: 'get',
    params
  })
}
