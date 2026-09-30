#ifndef WEBFORGE_OHOS_SOCKET_COMPAT_H
#define WEBFORGE_OHOS_SOCKET_COMPAT_H

#include <sys/socket.h>

/* SDK CMSG_NXTHDR compares size_t with a signed pointer difference. */
#undef CMSG_NXTHDR
#define CMSG_NXTHDR(mhdr, cmsg) \
    ((cmsg)->cmsg_len < sizeof(struct cmsghdr) || \
     __CMSG_LEN(cmsg) + sizeof(struct cmsghdr) >= \
         (size_t) (__MHDR_END(mhdr) - (unsigned char *) (cmsg)) \
     ? 0 : (struct cmsghdr *) __CMSG_NEXT(cmsg))

#endif
