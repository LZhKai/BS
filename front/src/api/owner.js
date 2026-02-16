import request from './request'

export const getOwnerList = () => {
  return request({
    url: '/owner/list',
    method: 'get'
  })
}

export const getOwnerPage = (params) => {
  return request({
    url: '/owner/page',
    method: 'get',
    params
  })
}

export const getOwnerById = (id) => {
  return request({
    url: `/owner/${id}`,
    method: 'get'
  })
}

export const saveOwner = (data) => {
  return request({
    url: '/owner',
    method: 'post',
    data
  })
}

export const updateOwner = (id, data) => {
  return request({
    url: `/owner/${id}`,
    method: 'put',
    data
  })
}

export const deleteOwner = (id) => {
  return request({
    url: `/owner/${id}`,
    method: 'delete'
  })
}
