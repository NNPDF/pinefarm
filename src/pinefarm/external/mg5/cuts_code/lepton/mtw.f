c     cut on the transverse mass of W bosons
      do i=3,nexternal
        do j=i+1,nexternal
          if (is_a_lm_reco(i) .or. is_a_lp_reco(i) .or.
     &        is_a_lm_reco(j) .or. is_a_lp_reco(j)) then
            if (abs(ipdg(i)+ipdg(j)).eq.1) then
              xmtw=2d0*sqrt((p(1,i)**2+p(2,i)**2)*
     &                      (p(1,j)**2+p(2,j)**2))-
     &             2d0*(p(1,i)*p(1,j)+p(2,i)*p(2,j))
              if (xmtw.lt.(({})**2)) then
                passcuts_leptons=.false.
                return
              endif
            endif
          endif
        enddo
      enddo
