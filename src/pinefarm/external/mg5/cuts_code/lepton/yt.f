c     cut on top particles
      do i=1,nexternal
        if (ipdg(i).eq.6 .or. ipdg(i).eq.-6) then
          if (abs(atanh(p_(3,i)/p(0,i)))
     &        .gt. {}) then
            passcuts_leptons=.false.
            return
          endif
        endif
      enddo
